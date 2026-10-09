"""Risk-assessed Change Plan Engine synthesizing step-by-step implementation plans."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import networkx as nx

from repopeek.storage import DualStorageEngine


class ChangePlanEngine:
    """Generates structured, risk-assessed implementation plans for engineering tasks."""

    def __init__(self, repo_root: Path | str, graph: nx.DiGraph, storage: DualStorageEngine | None = None):
        self.repo_root = Path(repo_root).resolve()
        self.graph = graph
        self.storage = storage

    def _resolve_target_symbols(self, task: str) -> list[tuple[str, dict[str, Any]]]:
        """Finds target symbols in the graph matching the task query."""
        tokens = set(re.findall(r"[a-zA-Z0-9_]+", task.lower()))
        matches: list[tuple[float, str, dict[str, Any]]] = []

        for node_id, data in self.graph.nodes(data=True):
            label = data.get("label", "").lower()
            fp = data.get("file_path", "").lower()
            score = 0.0
            for t in tokens:
                if len(t) < 3:
                    continue
                if t in label:
                    score += 5.0
                if t in node_id.lower():
                    score += 3.0
                if t in fp:
                    score += 2.0
            if score > 0.0:
                matches.append((score, node_id, data))

        matches.sort(key=lambda x: x[0], reverse=True)
        if matches:
            return [(item[1], item[2]) for item in matches[:3]]

        # Fallback to first non-external symbol
        fallback = []
        for node_id, data in self.graph.nodes(data=True):
            if not data.get("external") and data.get("file_path"):
                fallback.append((node_id, data))
                if len(fallback) >= 2:
                    break
        return fallback

    def generate_plan(self, task: str) -> dict[str, Any]:
        """Synthesizes risk level, caller impact, co-changes, and structured Markdown change plan."""
        targets = self._resolve_target_symbols(task)
        if not targets:
            return {
                "task": task,
                "risk_level": "LOW",
                "affected_callers": 0,
                "table_writes": 0,
                "plan_markdown": f"# Change Plan: {task}\n\n- Risk Level: LOW\n- No specific targets resolved in repository.",
            }

        target_ids = [t[0] for t in targets]
        affected_callers: list[str] = []
        table_writes: list[str] = []
        co_changed_tests: list[str] = []

        # 1. Blast radius & callers
        for tid in target_ids:
            if self.storage:
                upstream = self.storage.query_upstream_blast_radius(tid, max_depth=3)
                for u in upstream:
                    affected_callers.append(u.get("label") or u.get("node_id"))
            else:
                for u, _ in self.graph.in_edges(tid):
                    affected_callers.append(self.graph.nodes[u].get("label", u))

            # Database writes
            node_data = self.graph.nodes.get(tid, {})
            table_writes.extend(node_data.get("writes", []))

            # Co-changed files and tests
            for _, v, edge_data in self.graph.out_edges(tid, data=True):
                if edge_data.get("relation") == "CO_CHANGED_WITH":
                    fp = self.graph.nodes[v].get("file_path", v)
                    co_changed_tests.append(fp)

        affected_callers = list(dict.fromkeys(affected_callers))
        table_writes = list(dict.fromkeys(table_writes))
        co_changed_tests = list(dict.fromkeys(co_changed_tests))

        # 2. Risk assessment
        caller_count = len(affected_callers)
        write_count = len(table_writes)
        if caller_count >= 5 or write_count >= 2:
            risk = "HIGH"
        elif caller_count >= 2 or write_count >= 1:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        # 3. Assemble Plan Markdown
        md_lines = [
            f"# Change Plan: {task}",
            "",
            f"- **Risk Level**: {risk} ({caller_count} callers affected, {write_count} database entities modified)",
            f"- **Target Symbols**: {', '.join(t[1].get('label', t[0]) for t in targets)}",
            "",
            "## Step 1: Pre-flight Verification",
            "- Inspect current signatures and contracts of target symbols.",
        ]

        for tid, data in targets:
            fp = data.get("file_path", "unknown")
            sline = data.get("start_line", 1)
            eline = data.get("end_line", 1)
            lbl = data.get("label", tid)
            md_lines.append(f"  - Verify `{lbl}` in `{fp}` (Lines {sline}-{eline}).")

        md_lines.extend([
            "",
            "## Step 2: Implementation Sequence",
            "- Execute targeted refactoring or logic enhancement within the focused files.",
            "- Ensure no unintended breaking changes to public parameter contracts.",
        ])

        if table_writes:
            md_lines.extend([
                "",
                "## Step 3: Database & State Entity Verification",
                f"- Database writes affected: {', '.join(f'`{w}`' for w in table_writes)}.",
                "- Verify all foreign key integrity and transactional isolation boundaries.",
            ])
        else:
            md_lines.extend([
                "",
                "## Step 3: Call-site and Boundary Verification",
                f"- Preserved Callers: {', '.join(f'`{c}`' for c in affected_callers[:5]) or 'No external callers impacted'}.",
            ])

        md_lines.extend([
            "",
            "## Step 4: Synchronized Co-Change & Regression Testing",
        ])

        if co_changed_tests:
            for t_file in co_changed_tests[:4]:
                md_lines.append(f"- Run test suite for temporally coupled file: `{t_file}`")
        else:
            md_lines.append("- Execute project pytest / test suite across affected modules.")

        plan_md = "\n".join(md_lines)

        return {
            "task": task,
            "risk_level": risk,
            "affected_callers": caller_count,
            "table_writes": write_count,
            "plan_markdown": plan_md,
            "targets": target_ids,
            "co_changes": co_changed_tests,
        }


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    G = nx.DiGraph()
    G.add_node("py:billing.py::create_invoice", label="create_invoice", kind="function", file_path="billing.py", writes=["invoices"])
    G.add_node("py:api.py::checkout", label="checkout", kind="function", file_path="api.py")
    G.add_edge("py:api.py::checkout", "py:billing.py::create_invoice", relation="CALLS")

    engine = ChangePlanEngine(".", G)
    plan = engine.generate_plan("Enhance create_invoice with retry logic")
    assert plan["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert "create_invoice" in plan["plan_markdown"]
    assert "Step 1: Pre-flight Verification" in plan["plan_markdown"]
    print("repopeek.context.planner self-test passed!")
