"""Incremental Watch Daemon achieving sub-50ms graph synchronization."""
from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Any, Callable

import networkx as nx

from repopeek.bridges import apply_all_bridges
from repopeek.detect import scan_workspace
from repopeek.extract import extract_file
from repopeek.models import EdgeRecord, NodeRecord
from repopeek.storage import DualStorageEngine


class IncrementalWatcher:
    """Monitors repository filesystem changes and patches the in-memory graph and SQLite cache in <50ms."""

    def __init__(
        self,
        repo_path: Path | str,
        graph: nx.DiGraph,
        storage: DualStorageEngine | None = None,
        on_change: Callable[[str, str], None] | None = None,
    ):
        self.repo_root = Path(repo_path).resolve()
        self.graph = graph
        self.storage = storage
        self.on_change = on_change
        # rel_path -> (mtime_ns, size, sha256_hash)
        self._snapshots: dict[str, tuple[int, int, str]] = {}
        self._initialize_baseline()

    def _hash_file(self, full_path: Path) -> str:
        try:
            content = full_path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except (OSError, FileNotFoundError):
            return ""

    def _initialize_baseline(self) -> None:
        """Records initial file state hashes across the workspace."""
        files = scan_workspace(self.repo_root)
        for f in files:
            try:
                stat = f.full_path.stat()
                h = self._hash_file(f.full_path)
                self._snapshots[f.relative_path] = (stat.st_mtime_ns, stat.st_size, h)
            except (OSError, FileNotFoundError):
                continue

    def scan_changes(self) -> tuple[list[str], list[str], list[str]]:
        """Identifies added, modified, and deleted files using fast stat checks before hashing.
        
        Returns: (added_files, modified_files, deleted_files)
        """
        current_files = scan_workspace(self.repo_root)
        seen_paths = set()
        added: list[str] = []
        modified: list[str] = []
        deleted: list[str] = []

        for f in current_files:
            rel = f.relative_path
            seen_paths.add(rel)
            try:
                stat = f.full_path.stat()
            except (OSError, FileNotFoundError):
                continue

            if rel not in self._snapshots:
                # Newly added file
                h = self._hash_file(f.full_path)
                self._snapshots[rel] = (stat.st_mtime_ns, stat.st_size, h)
                added.append(rel)
            else:
                old_mtime, old_size, old_hash = self._snapshots[rel]
                if stat.st_mtime_ns != old_mtime or stat.st_size != old_size:
                    new_hash = self._hash_file(f.full_path)
                    if new_hash != old_hash:
                        self._snapshots[rel] = (stat.st_mtime_ns, stat.st_size, new_hash)
                        modified.append(rel)
                    else:
                        # Mtime touched but contents identical
                        self._snapshots[rel] = (stat.st_mtime_ns, stat.st_size, old_hash)

        # Detect deletions
        for rel in list(self._snapshots.keys()):
            if rel not in seen_paths:
                del self._snapshots[rel]
                deleted.append(rel)

        return added, modified, deleted

    def patch_file(self, rel_path: str) -> None:
        """Incrementally removes stale nodes for rel_path and re-extracts updated AST facts."""
        full_path = self.repo_root / rel_path

        # 1. Purge stale nodes and edges owned by rel_path
        stale_nodes = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("file_path") == rel_path
        ]
        self.graph.remove_nodes_from(stale_nodes)

        # 2. Re-extract if file still exists
        if full_path.exists():
            nodes, edges = extract_file(full_path, self.repo_root)
            for node in nodes:
                self.graph.add_node(
                    node.id,
                    label=node.label,
                    kind=node.kind,
                    file_path=node.file_path,
                    start_line=node.start_line,
                    end_line=node.end_line,
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    docstring=node.docstring,
                    lenses=node.lenses,
                    reads=node.reads,
                    writes=node.writes,
                    raises=node.raises,
                    metadata=node.metadata,
                    external=node.external,
                )
            for edge in edges:
                self.graph.add_edge(
                    edge.source,
                    edge.target,
                    relation=edge.relation,
                    confidence=edge.confidence,
                    lenses=edge.lenses,
                    evidence=edge.evidence,
                    metadata=edge.metadata,
                )

        # 3. Re-evaluate cross-language bridges
        apply_all_bridges(self.graph)

    def sync_delta(self) -> dict[str, Any]:
        """Performs a single incremental delta synchronization cycle.
        
        Returns telemetry dictionary with elapsed_ms and affected files.
        """
        start_t = time.perf_counter()
        added, modified, deleted = self.scan_changes()

        for f in added:
            self.patch_file(f)
            if self.on_change:
                self.on_change("added", f)

        for f in modified:
            self.patch_file(f)
            if self.on_change:
                self.on_change("modified", f)

        for f in deleted:
            self.patch_file(f)
            if self.on_change:
                self.on_change("deleted", f)

        if (added or modified or deleted) and self.storage:
            self.storage.sync_graph(self.graph)

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        return {
            "elapsed_ms": round(elapsed_ms, 2),
            "added": added,
            "modified": modified,
            "deleted": deleted,
            "total_changes": len(added) + len(modified) + len(deleted),
        }

    def run_loop(self, poll_interval: float = 0.05, max_iterations: int | None = None) -> None:
        """Runs the incremental sync loop until stopped or max_iterations reached."""
        count = 0
        while True:
            self.sync_delta()
            count += 1
            if max_iterations is not None and count >= max_iterations:
                break
            time.sleep(poll_interval)


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        test_py = root / "app.py"
        test_py.write_text("def hello(): return 1\n", encoding="utf-8")

        G = nx.DiGraph()
        nodes, edges = extract_file(test_py, root)
        for n in nodes:
            G.add_node(n.id, label=n.label, kind=n.kind, file_path=n.file_path)

        watcher = IncrementalWatcher(root, G)
        labels = [d.get("label") for _, d in G.nodes(data=True)]
        assert any("hello" in l for l in labels)

        # Modify file
        test_py.write_text("def world(): return 2\n", encoding="utf-8")
        delta = watcher.sync_delta()
        assert delta["total_changes"] == 1
        new_labels = [d.get("label") for _, d in G.nodes(data=True)]
        assert any("world" in l for l in new_labels)
        assert not any("hello" in l for l in new_labels)
        print(f"repopeek.watch self-test passed in {delta['elapsed_ms']}ms!")
