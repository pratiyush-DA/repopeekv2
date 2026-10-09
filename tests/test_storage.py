"""Unit tests for Phase 3 Storage and Incremental Watch Engine."""
from __future__ import annotations

from pathlib import Path
import tempfile
import networkx as nx
import pytest

from repopeek.detect import scan_workspace
from repopeek.extract import extract_file
from repopeek.storage import DualStorageEngine
from repopeek.watch import IncrementalWatcher


def test_dual_storage_cte_queries():
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = DualStorageEngine(repopeek_dir=tmp_dir)

        # Build chain: A -> B -> C -> D
        G = nx.DiGraph()
        G.add_node("py:a.py::fn_a", label="fn_a", kind="function", file_path="a.py", start_line=1, end_line=10)
        G.add_node("py:b.py::fn_b", label="fn_b", kind="function", file_path="b.py", start_line=1, end_line=10)
        G.add_node("py:c.py::fn_c", label="fn_c", kind="function", file_path="c.py", start_line=1, end_line=10)
        G.add_node("py:d.py::fn_d", label="fn_d", kind="function", file_path="d.py", start_line=1, end_line=10)

        G.add_edge("py:a.py::fn_a", "py:b.py::fn_b", relation="CALLS")
        G.add_edge("py:b.py::fn_b", "py:c.py::fn_c", relation="CALLS")
        G.add_edge("py:c.py::fn_c", "py:d.py::fn_d", relation="CALLS")

        storage.sync_graph(G)

        # Upstream blast radius of D (should trace C, B, A)
        upstream = storage.query_upstream_blast_radius("py:d.py::fn_d", max_depth=4)
        upstream_ids = [u["node_id"] for u in upstream]
        assert "py:c.py::fn_c" in upstream_ids
        assert "py:b.py::fn_b" in upstream_ids
        assert "py:a.py::fn_a" in upstream_ids

        # Downstream reachability from A (should trace B, C, D)
        downstream = storage.query_downstream_reachability("py:a.py::fn_a", max_depth=4)
        downstream_ids = [d["node_id"] for d in downstream]
        assert "py:b.py::fn_b" in downstream_ids
        assert "py:c.py::fn_c" in downstream_ids
        assert "py:d.py::fn_d" in downstream_ids

        # Symbol lookup
        results = storage.lookup_symbol("fn_b")
        assert len(results) == 1
        assert results[0]["id"] == "py:b.py::fn_b"
        assert results[0]["label"] == "fn_b"


def test_incremental_watcher_sync():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        module_file = root / "math_ops.py"
        module_file.write_text("def add(x, y):\n    return x + y\n", encoding="utf-8")

        G = nx.DiGraph()
        nodes, edges = extract_file(module_file, root)
        for n in nodes:
            G.add_node(n.id, label=n.label, kind=n.kind, file_path=n.file_path)

        storage = DualStorageEngine(repopeek_dir=root / ".repopeek")
        storage.sync_graph(G)

        watcher = IncrementalWatcher(root, G, storage=storage)

        # Baseline: no changes
        delta = watcher.sync_delta()
        assert delta["total_changes"] == 0

        # Modify file: add subtract
        module_file.write_text("def add(x, y):\n    return x + y\n\ndef sub(x, y):\n    return x - y\n", encoding="utf-8")
        delta2 = watcher.sync_delta()
        assert delta2["total_changes"] == 1
        assert "math_ops.py" in delta2["modified"]
        assert delta2["elapsed_ms"] < 100.0  # sub-100ms verification

        # Check graph updated
        labels = [d.get("label") for _, d in G.nodes(data=True)]
        assert any("sub" in l for l in labels)
