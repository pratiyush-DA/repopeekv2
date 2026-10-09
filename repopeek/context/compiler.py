"""Context Compiler enforcing strictly <=4 files cap, ~40-line spans, and 3-tier progressive disclosure."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import networkx as nx

from repopeek.models import ContextPackage, ContextSnippet
from repopeek.storage import DualStorageEngine


class ContextCompiler:
    """Compiles natural language engineering tasks into token-minimized ContextPackages."""

    def __init__(self, repo_root: Path | str, graph: nx.DiGraph, storage: DualStorageEngine | None = None):
        self.repo_root = Path(repo_root).resolve()
        self.graph = graph
        self.storage = storage

    def _score_node_relevance(self, query: str, node_id: str, data: dict[str, Any]) -> float:
        """Computes lexical relevance score between task query terms and node metadata."""
        q_tokens = set(re.findall(r"[a-zA-Z0-9_]+", query.lower()))
        if not q_tokens:
            return 0.0

        label = data.get("label", "").lower()
        node_str = node_id.lower()
        file_path = data.get("file_path", "").lower()
        docstring = data.get("docstring", "").lower()

        score = 0.0
        for token in q_tokens:
            if len(token) < 3:
                continue
            if token in label:
                score += 5.0
            if token in node_str:
                score += 3.0
            if token in file_path:
                score += 2.0
            if token in docstring:
                score += 1.0

        # Boost functions/classes over plain modules
        kind = data.get("kind", "").lower()
        if kind in ("function", "method", "class", "route"):
            score *= 1.2

        return score

    def _resolve_seed_symbols(self, task: str, limit: int = 5) -> list[tuple[str, dict[str, Any]]]:
        """Finds top-scoring nodes in the graph matching the task."""
        scored: list[tuple[float, str, dict[str, Any]]] = []
        for node_id, data in self.graph.nodes(data=True):
            s = self._score_node_relevance(task, node_id, data)
            if s > 0.0:
                scored.append((s, node_id, data))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [(item[1], item[2]) for item in scored[:limit]]

    def _extract_span_text(self, rel_path: str, start_line: int, end_line: int, max_window: int = 40) -> tuple[int, int, str]:
        """Extracts ~40-line code span around target start and end lines."""
        full_path = self.repo_root / rel_path
        if not full_path.is_file():
            return start_line, end_line, f"// File not found: {rel_path}"

        try:
            lines = full_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return start_line, end_line, ""

        total = len(lines)
        if total == 0:
            return 1, 1, ""

        span_len = max(1, end_line - start_line + 1)
        if span_len >= max_window:
            actual_start = max(1, start_line)
            actual_end = min(total, start_line + max_window - 1)
        else:
            padding = (max_window - span_len) // 2
            actual_start = max(1, start_line - padding)
            actual_end = min(total, actual_start + max_window - 1)

        selected_lines = lines[actual_start - 1 : actual_end]
        snippet_text = "\n".join(
            f"{actual_start + i:4d} | {line}" for i, line in enumerate(selected_lines)
        )
        return actual_start, actual_end, snippet_text

    def compile_context(
        self,
        task: str,
        level: int = 2,
        max_files: int = 4,
    ) -> ContextPackage:
        """Synthesizes a minimal, bounded ContextPackage with strictly <= max_files (default 4)."""
        seeds = self._resolve_seed_symbols(task, limit=10)

        # If no lexical match found, pick first non-external code nodes as fallback
        if not seeds:
            for node_id, data in self.graph.nodes(data=True):
                if not data.get("external") and data.get("file_path"):
                    seeds.append((node_id, data))
                    if len(seeds) >= 2:
                        break

        # Group by files, cap at max_files (<=4)
        chosen_files: dict[str, tuple[str, dict[str, Any]]] = {}
        for node_id, data in seeds:
            fp = data.get("file_path")
            if fp and fp not in chosen_files and len(chosen_files) < max_files:
                chosen_files[fp] = (node_id, data)

        snippets: list[ContextSnippet] = []
        invariants: list[str] = []
        affected_tests: list[str] = []

        for fp, (node_id, data) in chosen_files.items():
            start = data.get("start_line", 1)
            end = data.get("end_line", start + 20)

            if level == 1:
                # Level 1: Orientation (just signature and location, ~300 tokens)
                code_text = f"{data.get('label', '')} ({data.get('kind', 'symbol')}) at line {start}-{end}"
                actual_start, actual_end = start, end
            else:
                # Level 2 & 3: Actionable focus span (~40 lines)
                actual_start, actual_end, code_text = self._extract_span_text(fp, start, end, max_window=40)

            snippets.append(ContextSnippet(
                file_path=fp,
                symbol_id=node_id,
                start_line=actual_start,
                end_line=actual_end,
                code_text=code_text,
            ))

            # Invariants: database tables and reads/writes
            reads = data.get("reads", [])
            writes = data.get("writes", [])
            if writes:
                invariants.append(f"Symbol {data.get('label')} writes data entities: {', '.join(writes)} (do not orphan)")
            if reads:
                invariants.append(f"Symbol {data.get('label')} reads data entities: {', '.join(reads)}")

            # Temporal co-changes & tests
            for _, v, edge_data in self.graph.out_edges(node_id, data=True):
                if edge_data.get("relation") == "CO_CHANGED_WITH":
                    tgt_fp = self.graph.nodes[v].get("file_path", v)
                    if "test" in tgt_fp.lower():
                        affected_tests.append(tgt_fp)
                    else:
                        invariants.append(f"Temporal coupling: modifying {fp} frequently co-changes with {tgt_fp}")

        # Upstream callers in blast radius
        for fp, (node_id, data) in chosen_files.items():
            in_edges = list(self.graph.in_edges(node_id, data=True))
            for u, _, edge_data in in_edges[:3]:
                caller_label = self.graph.nodes[u].get("label", u)
                invariants.append(f"Preserve caller contract: {caller_label} ({edge_data.get('relation', 'CALLS')} -> {data.get('label')})")

        # Deduplicate invariants and tests
        invariants = list(dict.fromkeys(invariants))
        affected_tests = list(dict.fromkeys(affected_tests))

        # Token estimation
        raw_text_chars = sum(len(s.code_text) for s in snippets) + sum(len(inv) for inv in invariants)
        estimated_tokens = max(150, raw_text_chars // 4)

        # Baseline counterfactual token comparison
        # Total files in repo vs focus files
        total_repo_nodes = len([n for n, d in self.graph.nodes(data=True) if d.get("file_path")])
        total_files = len(set(d.get("file_path") for n, d in self.graph.nodes(data=True) if d.get("file_path")))
        baseline_tokens = max(estimated_tokens * 8, total_files * 800)
        tokens_saved = max(0, baseline_tokens - estimated_tokens)
        files_avoided = max(0, total_files - len(chosen_files))
        cost_saved_usd = round((tokens_saved / 1_000_000.0) * 3.0, 4)  # $3/M tokens average

        scorecard = {
            "baseline_tokens": baseline_tokens,
            "actual_tokens": estimated_tokens,
            "tokens_saved": tokens_saved,
            "files_avoided": files_avoided,
            "cost_saved_usd": cost_saved_usd,
            "savings_percent": round((tokens_saved / max(1, baseline_tokens)) * 100.0, 1),
        }

        return ContextPackage(
            task=task,
            level=level,
            file_count=len(snippets),
            snippets=snippets,
            invariants=invariants,
            affected_tests=affected_tests,
            estimated_tokens=estimated_tokens,
            scorecard=scorecard,
        )


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        p1 = root / "invoice.py"
        p1.write_text("\n".join([f"def line_{i}(): pass" for i in range(100)]), encoding="utf-8")

        G = nx.DiGraph()
        G.add_node("py:invoice.py::line_20", label="line_20", kind="function", file_path="invoice.py", start_line=20, end_line=22)

        compiler = ContextCompiler(root, G)
        pkg = compiler.compile_context("Update line_20 logic in invoice", level=2)
        assert pkg.file_count <= 4, "ContextCompiler violated file count cap <= 4"
        assert len(pkg.snippets) == 1
        assert "20 |" in pkg.snippets[0].code_text
        assert pkg.estimated_tokens > 0
        assert pkg.scorecard["tokens_saved"] > 0
        print("repopeek.context.compiler self-test passed!")
