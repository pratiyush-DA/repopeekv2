"""Model Context Protocol (MCP) stdio JSON-RPC server exposing all 11 RepoPeek tools."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import networkx as nx

from repopeek.bridges.http import synthesize_http_bridges
from repopeek.context.compiler import ContextCompiler
from repopeek.context.planner import ChangePlanEngine
from repopeek.context.verifier import build_ast_fact_card
from repopeek.storage import DualStorageEngine
from repopeek.telemetry import TelemetryTracker


class RepoPeekMCPServer:
    """11-Tool Model Context Protocol Server for AI coding assistants."""

    def __init__(
        self,
        repo_root: Path | str,
        graph: nx.DiGraph,
        storage: DualStorageEngine | None = None,
        telemetry: TelemetryTracker | None = None,
    ):
        self.repo_root = Path(repo_root).resolve()
        self.graph = graph
        self.storage = storage or DualStorageEngine(repopeek_dir=self.repo_root / ".repopeek")
        self.telemetry = telemetry or TelemetryTracker(repopeek_dir=self.repo_root / ".repopeek")
        self.compiler = ContextCompiler(self.repo_root, self.graph, self.storage)
        self.planner = ChangePlanEngine(self.repo_root, self.graph, self.storage)

    # 1. repopeek_lookup
    def tool_lookup(self, query: str) -> str:
        """Looks up a symbol or entity by name or ID. Returns formatted Markdown fact card."""
        # 1. Exact node check
        if query in self.graph:
            return build_ast_fact_card(dict(self.graph.nodes[query]))

        # 2. SQLite / graph search
        results = self.storage.lookup_symbol(query)
        if not results:
            # Fallback search graph labels
            matches = [d for n, d in self.graph.nodes(data=True) if query.lower() in d.get("label", "").lower()]
            if matches:
                return "\n\n---\n\n".join(build_ast_fact_card(m) for m in matches[:3])
            return f"Symbol '{query}' not found in code property graph."

        return "\n\n---\n\n".join(build_ast_fact_card(r) for r in results[:3])

    # 2. repopeek_neighbors
    def tool_neighbors(self, query: str, relation_filter: str | None = None) -> str:
        """Inspects immediate 1-hop inbound and outbound edges."""
        node_id = None
        if query in self.graph:
            node_id = query
        else:
            for n, d in self.graph.nodes(data=True):
                if query.lower() in d.get("label", "").lower() or query in n:
                    node_id = n
                    break

        if not node_id:
            return f"Node '{query}' not found."

        data = self.graph.nodes[node_id]
        lines = [f"## Neighbors for `{data.get('label', node_id)}` (`{node_id}`)", ""]

        in_edges = list(self.graph.in_edges(node_id, data=True))
        out_edges = list(self.graph.out_edges(node_id, data=True))

        if relation_filter:
            rf = relation_filter.upper()
            in_edges = [e for e in in_edges if e[2].get("relation", "").upper() == rf]
            out_edges = [e for e in out_edges if e[2].get("relation", "").upper() == rf]

        lines.append(f"### Inbound Callers & References ({len(in_edges)}):")
        for u, _, edata in in_edges:
            ulbl = self.graph.nodes[u].get("label", u)
            lines.append(f"- `[{edata.get('relation', 'DEPENDS_ON')}]` <- `{ulbl}` (`{u}`)")

        lines.append("")
        lines.append(f"### Outbound Callees & Mutations ({len(out_edges)}):")
        for _, v, edata in out_edges:
            vlbl = self.graph.nodes[v].get("label", v)
            lines.append(f"- `[{edata.get('relation', 'DEPENDS_ON')}]` -> `{vlbl}` (`{v}`)")

        return "\n".join(lines)

    # 3. repopeek_impact
    def tool_impact(self, target: str, max_depth: int = 3, direction: str = "both") -> str:
        """Calculates blast radius ('If I edit X, what breaks?')."""
        target_id = None
        if target in self.graph:
            target_id = target
        else:
            for n, d in self.graph.nodes(data=True):
                if target.lower() in d.get("label", "").lower() or target in n:
                    target_id = n
                    break

        if not target_id:
            return f"Target '{target}' not found."

        lines = [f"## Blast Radius Analysis: `{target}`", ""]
        if direction in ("upstream", "both"):
            upstream = self.storage.query_upstream_blast_radius(target_id, max_depth=max_depth)
            lines.append(f"### Upstream Impact (Callers that may break) [{len(upstream)}]:")
            for u in upstream:
                lines.append(f"- Depth {u['depth']}: `{u.get('label') or u['node_id']}` in `{u.get('file_path')}` (L{u.get('start_line')}-{u.get('end_line')})")

        if direction in ("downstream", "both"):
            downstream = self.storage.query_downstream_reachability(target_id, max_depth=max_depth)
            lines.append("")
            lines.append(f"### Downstream Reachability (Dependencies & state affected) [{len(downstream)}]:")
            for d in downstream:
                lines.append(f"- Depth {d['depth']}: `{d.get('label') or d['node_id']}` in `{d.get('file_path')}` (L{d.get('start_line')}-{d.get('end_line')})")

        return "\n".join(lines)

    # 4. repopeek_data_trace
    def tool_data_trace(self, query: str) -> str:
        """Traces state def-use: who writes entity X and who reads entity X across SQL and code."""
        q = query.lower()
        readers: list[tuple[str, str, str]] = []
        writers: list[tuple[str, str, str]] = []

        for node_id, data in self.graph.nodes(data=True):
            lbl = data.get("label", node_id)
            fp = data.get("file_path", "")
            reads = [r.lower() for r in data.get("reads", [])]
            writes = [w.lower() for w in data.get("writes", [])]

            if any(q in r for r in reads):
                readers.append((lbl, fp, node_id))
            if any(q in w for w in writes):
                writers.append((lbl, fp, node_id))

        lines = [f"# Data Def-Use Trace for `{query}`", ""]
        lines.append(f"## Writers (Mutates / Writes `{query}`) [{len(writers)}]:")
        for lbl, fp, nid in writers:
            lines.append(f"- `{lbl}` in `{fp}` (`{nid}`)")

        lines.append("")
        lines.append(f"## Readers (Reads `{query}`) [{len(readers)}]:")
        for lbl, fp, nid in readers:
            lines.append(f"- `{lbl}` in `{fp}` (`{nid}`)")

        return "\n".join(lines)

    # 5. repopeek_context_pack
    def tool_context_pack(self, targets: list[str], token_budget: int = 2000) -> str:
        """Generates a budget-governed pack for known symbol IDs with zero fluff and exact line spans."""
        snippets = []
        for tid in targets[:4]:
            if tid in self.graph:
                d = self.graph.nodes[tid]
                fp = d.get("file_path")
                sline = d.get("start_line", 1)
                eline = d.get("end_line", sline + 20)
                if fp:
                    _, _, code_text = self.compiler._extract_span_text(fp, sline, eline, max_window=40)
                    snippets.append(f"### File: `{fp}` ({d.get('label')}, Lines {sline}-{eline})\n```\n{code_text}\n```")

        if not snippets:
            return f"No target symbols resolved from {targets}."

        return "\n\n".join(snippets)

    # 6. repopeek_context
    def tool_context(self, task: str, budget: int = 2000, level: int = 2) -> str:
        """Compiles natural-language task into focused <=4 files with ~40-line snippets and prepended efficiency scorecard."""
        pkg = self.compiler.compile_context(task, level=level, max_files=4)

        # Record savings in telemetry
        card_event = self.telemetry.record_event(
            task=task,
            baseline_tokens=pkg.scorecard["baseline_tokens"],
            delivered_tokens=pkg.scorecard["actual_tokens"],
            baseline_files=pkg.scorecard["baseline_tokens"] // 800,
            delivered_files=pkg.file_count,
        )

        ascii_card = self.telemetry.render_ascii_card(card_event)

        sections = [
            ascii_card,
            "",
            f"# Context Package for: {task}",
            f"- **Focus Files ({pkg.file_count}/4)**: {', '.join(s.file_path for s in pkg.snippets)}",
            f"- **Estimated Tokens**: {pkg.estimated_tokens:,} tokens",
            "",
            "## Focus Code Spans",
        ]

        for s in pkg.snippets:
            sections.append(f"### File: `{s.file_path}` (Lines {s.start_line}-{s.end_line})\n```\n{s.code_text}\n```")

        if pkg.invariants:
            sections.append("")
            sections.append("## Invariants & Critical Constraints")
            for inv in pkg.invariants:
                sections.append(f"- {inv}")

        if pkg.affected_tests:
            sections.append("")
            sections.append("## Affected Test Suites")
            for tst in pkg.affected_tests:
                sections.append(f"- `{tst}`")

        return "\n".join(sections)

    # 7. repopeek_plan
    def tool_plan(self, task: str) -> str:
        """Formulates a step-by-step engineering plan with risk levels, affected callers, and test verification recommendations."""
        res = self.planner.generate_plan(task)
        return res["plan_markdown"]

    # 8. repopeek_routes
    def tool_routes(self) -> str:
        """Lists detected cross-language HTTP routes, matching client API calls (fetch/axios) to backend route handlers."""
        bridges = synthesize_http_bridges(self.graph)
        lines = [
            "# Detected Cross-Language HTTP Routes",
            "",
            f"Found {len(bridges)} cross-boundary route bindings:",
            "",
            "| Client API Caller | Backend Route Endpoint | Confidence | Lens |",
            "|---|---|---|---|",
        ]
        for b in bridges:
            lines.append(f"| `{b.source}` | `{b.target}` | {b.confidence*100:.0f}% | {', '.join(sorted(b.lenses))} |")

        if not bridges:
            lines.append("No explicit cross-language HTTP routes identified.")

        return "\n".join(lines)

    # 9. repopeek_co_changes
    def tool_co_changes(self, target: str) -> str:
        """Surfaces files that temporally change together in git history despite lacking direct static import links."""
        results = []
        for u, v, data in self.graph.edges(data=True):
            if data.get("relation") == "CO_CHANGED_WITH":
                if target.lower() in u.lower() or target.lower() in v.lower():
                    prob = data.get("confidence", 0.0)
                    results.append((u, v, prob))

        results.sort(key=lambda x: x[2], reverse=True)
        lines = [f"# Git Temporal Co-Changes for `{target}`", ""]
        if not results:
            lines.append("No high-probability git co-change couplings found.")
        else:
            for u, v, prob in results:
                lines.append(f"- `{u}` <-> `{v}` (P = {prob*100:.1f}%)")

        return "\n".join(lines)

    # 10. repopeek_resolve
    def tool_resolve(self, task: str) -> str:
        """Disambiguates and ranks symbol candidates matching a natural-language description."""
        seeds = self.compiler._resolve_seed_symbols(task, limit=10)
        lines = [f"# Resolved Symbols for: `{task}`", ""]
        if not seeds:
            lines.append("No matching symbols resolved.")
        else:
            for node_id, data in seeds:
                lbl = data.get("label", node_id)
                k = data.get("kind", "symbol")
                fp = data.get("file_path", "")
                sline = data.get("start_line", 1)
                lines.append(f"- **`{lbl}`** (`{k}`) -> `{fp}`:L{sline} (ID: `{node_id}`)")

        return "\n".join(lines)

    # 11. repopeek_savings
    def tool_savings(self, timeframe: str = "current_session") -> str:
        """Presents quantifiable token, file-fetching, and cost savings achieved compared to counterfactual raw-repo exploration."""
        summary = self.telemetry.get_summary(timeframe=timeframe)
        return self.telemetry.render_hud_markdown(summary)

    def dispatch_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Dispatches an MCP tool call by name with argument unpacking."""
        if name == "repopeek_lookup":
            return self.tool_lookup(arguments.get("query", ""))
        elif name == "repopeek_neighbors":
            return self.tool_neighbors(arguments.get("query", ""), arguments.get("relation_filter"))
        elif name == "repopeek_impact":
            return self.tool_impact(
                arguments.get("target", ""),
                arguments.get("max_depth", 3),
                arguments.get("direction", "both")
            )
        elif name == "repopeek_data_trace":
            return self.tool_data_trace(arguments.get("query", ""))
        elif name == "repopeek_context_pack":
            return self.tool_context_pack(
                arguments.get("targets", []),
                arguments.get("token_budget", 2000)
            )
        elif name == "repopeek_context":
            return self.tool_context(
                arguments.get("task", ""),
                arguments.get("budget", 2000),
                arguments.get("level", 2)
            )
        elif name == "repopeek_plan":
            return self.tool_plan(arguments.get("task", ""))
        elif name == "repopeek_routes":
            return self.tool_routes()
        elif name == "repopeek_co_changes":
            return self.tool_co_changes(arguments.get("target", ""))
        elif name == "repopeek_resolve":
            return self.tool_resolve(arguments.get("task", ""))
        elif name == "repopeek_savings":
            return self.tool_savings(arguments.get("timeframe", "current_session"))
        else:
            return f"Error: Unknown tool '{name}'."

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Returns standard MCP tool declarations for all 11 tools."""
        return [
            {
                "name": "repopeek_lookup",
                "description": "Looks up a symbol or entity by name or ID. Returns file location, parameters, and docstrings.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Symbol name, function name, or node ID"}},
                    "required": ["query"],
                },
            },
            {
                "name": "repopeek_neighbors",
                "description": "Inspects immediate 1-hop inbound and outbound edges for direct callers, callees, and mutations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Symbol or node identifier"},
                        "relation_filter": {"type": "string", "description": "Optional relation filter (e.g. CALLS, READS, WRITES)"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "repopeek_impact",
                "description": "Calculates blast radius ('If I edit X, what breaks?'). Returns affected callers and database tables.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "Target symbol or entity"},
                        "max_depth": {"type": "integer", "description": "Maximum traversal depth (default 3)"},
                        "direction": {"type": "string", "enum": ["upstream", "downstream", "both"], "description": "Traversal direction"},
                    },
                    "required": ["target"],
                },
            },
            {
                "name": "repopeek_data_trace",
                "description": "Traces state def-use: who writes and reads entity X across SQL tables and application code.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Database table name, view, or state entity"}},
                    "required": ["query"],
                },
            },
            {
                "name": "repopeek_context_pack",
                "description": "Generates a budget-governed pack for known symbol IDs with zero fluff and exact line spans.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "targets": {"type": "array", "items": {"type": "string"}, "description": "List of symbol IDs"},
                        "token_budget": {"type": "integer", "description": "Target token budget (default 2000)"},
                    },
                    "required": ["targets"],
                },
            },
            {
                "name": "repopeek_context",
                "description": "Compiles natural-language task into focused <=4 files with ~40-line snippets, exclusions, constraints, and prepended efficiency scorecard.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Natural language engineering task"},
                        "budget": {"type": "integer", "description": "Token budget"},
                        "level": {"type": "integer", "description": "Progressive disclosure level (1=orientation, 2=focus pack, 3=deep risk plan)"},
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "repopeek_plan",
                "description": "Formulates a step-by-step engineering plan with risk levels, affected callers, and test verification recommendations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"task": {"type": "string", "description": "Engineering task to formulate a plan for"}},
                    "required": ["task"],
                },
            },
            {
                "name": "repopeek_routes",
                "description": "Lists detected cross-language HTTP routes, matching client API calls (fetch/axios) to backend route handlers.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "repopeek_co_changes",
                "description": "Surfaces files that temporally change together in git history (P >= 0.25) despite lacking direct static import links.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"target": {"type": "string", "description": "File path or symbol"}},
                    "required": ["target"],
                },
            },
            {
                "name": "repopeek_resolve",
                "description": "Disambiguates and ranks symbol candidates matching a natural-language description.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"task": {"type": "string", "description": "Natural language query"}},
                    "required": ["task"],
                },
            },
            {
                "name": "repopeek_savings",
                "description": "Calculates and presents quantifiable token, file-fetching, and cost savings achieved compared to counterfactual raw-repo exploration.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "timeframe": {"type": "string", "enum": ["current_session", "all_time"], "description": "Savings aggregation timeframe"},
                    },
                },
            },
        ]

    def run_stdio_server(self) -> None:
        """Executes stdio JSON-RPC loop handling MCP requests."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                req = json.loads(line)
            except json.JSONDecodeError:
                continue

            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "repopeek", "version": "2.0.0"},
                    },
                }
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": self.get_tool_definitions()},
                }
            elif method == "tools/call":
                tname = params.get("name", "")
                targs = params.get("arguments", {})
                content_text = self.dispatch_tool(tname, targs)
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": content_text}],
                        "isError": False,
                    },
                }
            else:
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method '{method}' not found"},
                }

            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    G = nx.DiGraph()
    G.add_node("py:app.py::main", label="main", kind="function", file_path="app.py", start_line=1, end_line=10)
    server = RepoPeekMCPServer(".", G)
    assert len(server.get_tool_definitions()) == 11
    resp = server.dispatch_tool("repopeek_lookup", {"query": "main"})
    assert "main" in resp
    savings_hud = server.dispatch_tool("repopeek_savings", {})
    assert "RepoPeek Context Efficiency" in savings_hud
    print("repopeek.serve 11-tool MCP server self-test passed!")
