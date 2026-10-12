"""Unified Command Line Interface for RepoPeek V2."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import networkx as nx

from repopeek.bridges import apply_all_bridges
from repopeek.build import build_graph_from_records
from repopeek.cluster import detect_communities
from repopeek.detect import scan_workspace
from repopeek.exporters import (
    export_callflow_html,
    export_canvas,
    export_cypher,
    export_graphml,
    export_interactive_html,
    export_markdown_wiki,
    export_obsidian_vault,
    export_svg,
)
from repopeek.extract import extract_file
from repopeek.global_graph import get_global_graph_path, list_global_repos
from repopeek.hooks import get_hook_status, install_hooks, uninstall_hooks
from repopeek.models import EdgeRecord, NodeRecord
from repopeek.prs import analyze_pr_impact, format_pr_dashboard, get_git_changed_files
from repopeek.reflect import reflect, save_result
from repopeek.serve import RepoPeekMCPServer
from repopeek.storage import DualStorageEngine
from repopeek.telemetry import TelemetryTracker
from repopeek.temporal import apply_co_change_edges, mine_git_co_changes
from repopeek.watch import IncrementalWatcher


def index_repository(
    repo_path: Path | str,
    repopeek_dir: Path | str | None = None,
    force: bool = False,
) -> tuple[nx.DiGraph, DualStorageEngine, TelemetryTracker]:
    """Discovers, parses, and indexes the entire codebase into a Semantic Code Property Graph."""
    root = Path(repo_path).resolve()
    base_dir = Path(repopeek_dir).resolve() if repopeek_dir else root / ".repopeek"
    storage = DualStorageEngine(repopeek_dir=base_dir)
    telemetry = TelemetryTracker(repopeek_dir=base_dir)

    files = scan_workspace(root)
    all_nodes: list[NodeRecord] = []
    all_edges: list[EdgeRecord] = []

    for f in files:
        nodes, edges = extract_file(f.full_path, root)
        all_nodes.extend(nodes)
        all_edges.extend(edges)

    graph = build_graph_from_records(all_nodes, all_edges)
    apply_all_bridges(graph)

    co_changes = mine_git_co_changes(root)
    if co_changes:
        apply_co_change_edges(graph, co_changes)

    detect_communities(graph)
    storage.sync_graph(graph, force=force)

    return graph, storage, telemetry


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="RepoPeek V2 - Semantic Code Property Graph Engine")
    parser.add_argument("cmd", nargs="?", help="Optional subcommand (e.g. install)")
    parser.add_argument("--platform", choices=["claude-code", "cursor", "antigravity", "copilot", "all"], help="Target AI assistant platform to configure")
    parser.add_argument("--repo-path", default=".", help="Path to target repository root (default: current directory)")
    parser.add_argument("--output-dir", default=".repopeek", help="Directory for storage and graph cache")
    parser.add_argument("--offline", action="store_true", help="Run deterministic offline indexing (zero LLM)")
    parser.add_argument("--watch", action="store_true", help="Start incremental watch daemon (<50ms sync on changes)")
    parser.add_argument("--serve-mcp", action="store_true", help="Start Model Context Protocol server")
    parser.add_argument("--serve-http", action="store_true", help="Start streamable HTTP ASGI/MCP server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio", help="MCP transport (default: stdio)")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP server bind host (default: 127.0.0.1)")
    parser.add_argument("--api-key", help="API key required for HTTP MCP access")

    # Workflow, PR & Experiential Commands
    parser.add_argument("--hook", choices=["install", "uninstall", "status"], help="Manage git lifecycle hooks")
    parser.add_argument("--prs", action="store_true", help="Analyze branch PR impact and blast radius")
    parser.add_argument("--base", default="main", help="Base branch for PR diff comparison (default: main)")
    parser.add_argument("--reflect", action="store_true", help="Compile experiential lessons into docs/LESSONS.md")
    parser.add_argument("--save-result", nargs="+", metavar="ITEM", help="Save experiential Q&A outcome (question [answer] [outcome])")
    parser.add_argument("--global-cmd", choices=["list", "path"], help="Query global multi-repo registry")

    # Instant Graph Queries
    parser.add_argument("--lookup", help="Look up symbol fact card by name or ID")
    parser.add_argument("--neighbors", help="Inspect immediate 1-hop inbound and outbound edges for symbol")
    parser.add_argument("--impact", help="Calculate blast radius tree for symbol")
    parser.add_argument("--depth", type=int, default=3, help="Max depth for blast radius traversal (default: 3)")
    parser.add_argument("--trace", help="Trace data def-use for table or variable")
    parser.add_argument("--context", help="Compile natural language task into focused <=4 files pack")
    parser.add_argument("--level", type=int, default=2, help="Progressive disclosure level (1=orientation, 2=focus, 3=deep)")
    parser.add_argument("--plan", help="Generate risk-assessed step-by-step engineering plan")
    parser.add_argument("--routes", action="store_true", help="List detected cross-language HTTP routes")
    parser.add_argument("--co-changes", help="Surface git temporal co-changes for file or symbol")
    parser.add_argument("--savings", action="store_true", help="Display quantifiable tokens and cost savings HUD")
    parser.add_argument("--path", nargs=2, metavar=("SOURCE", "TARGET"), help="Find shortest path between two symbols")
    parser.add_argument("--explain", metavar="SYMBOL", help="Detailed breakdown of a concept node")
    parser.add_argument("--query", metavar="QUESTION", help="Natural-language BFS/DFS graph search")
    parser.add_argument("--mode", default="bfs", choices=["bfs", "dfs"], help="Query traversal mode (default: bfs)")
    parser.add_argument("--diagnose", action="store_true", help="Audit graph health and integrity")
    parser.add_argument("--cycles", action="store_true", help="Detect circular dependency/import cycles")
    parser.add_argument("--force", action="store_true", help="Bypass anti-shrink protection guard")

    # Exporters & Viewers
    parser.add_argument("--view", action="store_true", help="Generate standalone interactive D3 HTML graph viewer")
    parser.add_argument("--serve", action="store_true", help="Start local HTTP server to preview interactive graph viewer")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve interactive web viewer")
    parser.add_argument("--export-obsidian", help="Export graph into an Obsidian Markdown vault")
    parser.add_argument("--export-callflow", help="Export Mermaid callflow and architecture HTML report")
    parser.add_argument("--export-wiki", help="Export agent-crawlable markdown wiki directory")
    parser.add_argument("--export-cypher", help="Export Neo4j/FalkorDB Cypher DDL and upsert file")
    parser.add_argument("--export-graphml", help="Export standard GraphML file (Gephi, yEd)")
    parser.add_argument("--export-canvas", help="Export Obsidian .canvas JSON file")
    parser.add_argument("--export-svg", help="Export vector SVG diagram")

    args = parser.parse_args(argv)
    repo_root = Path(args.repo_path).resolve()

    # Fast path: savings without re-indexing full repo if ledger exists
    if args.savings and not (args.lookup or args.impact or args.trace or args.context or args.plan or args.path or args.explain or args.query):
        telemetry = TelemetryTracker(repopeek_dir=repo_root / args.output_dir)
        summary = telemetry.get_summary(timeframe="all_time")
        print(telemetry.render_hud_markdown(summary))
        return 0

    if args.cmd == "install" or args.platform:
        from repopeek.installer import install_platform
        target_plat = args.platform or "all"
        res = install_platform(target_plat, repo_root)
        print(f"RepoPeek assistant configuration for '{target_plat}' completed successfully:")
        for cf in res["configured_files"]:
            print(f"- {cf}")
        return 0

    if args.hook:
        if args.hook == "install":
            res = install_hooks(repo_root)
            print(f"Git lifecycle hooks installation status: {res.get('status')} ({res.get('installed_hooks', res.get('message'))})")
        elif args.hook == "uninstall":
            res = uninstall_hooks(repo_root)
            print(f"Git lifecycle hooks uninstalled: {res}")
        elif args.hook == "status":
            st = get_hook_status(repo_root)
            print(f"Git lifecycle hooks: post-commit={st['post_commit']}, post-checkout={st['post_checkout']}, merge-driver={st['merge_driver']}")
        return 0

    if args.global_cmd:
        if args.global_cmd == "list":
            repos = list_global_repos()
            print(f"Global repositories ({len(repos)}):")
            for r in repos:
                print(f"- {r}")
        elif args.global_cmd == "path":
            print(f"Global graph storage path: {get_global_graph_path()}")
        return 0

    if args.save_result:
        q = args.save_result[0]
        a = args.save_result[1] if len(args.save_result) > 1 else ""
        outcome = args.save_result[2] if len(args.save_result) > 2 else "useful"
        rec_path = save_result(repo_root / args.output_dir, question=q, answer=a, outcome=outcome)
        print(f"Saved experiential result to {rec_path}")
        return 0

    if args.reflect:
        res = reflect(repo_root / args.output_dir, graph=None, out_markdown=repo_root / "docs" / "LESSONS.md")
        print(f"Synthesized {res['total_memories']} memories into {res['lessons_path']} (preferred: {len(res['preferred_nodes'])}, contested: {len(res['contested_nodes'])})")
        return 0

    # Index repository
    is_stdio_mcp = (args.serve_mcp and args.transport == "stdio") and not args.serve_http
    if is_stdio_mcp:
        orig_stdout = sys.stdout
        sys.stdout = sys.stderr
        try:
            graph, storage, telemetry = index_repository(repo_root, repopeek_dir=repo_root / args.output_dir, force=args.force)
        finally:
            sys.stdout = orig_stdout
    else:
        graph, storage, telemetry = index_repository(repo_root, repopeek_dir=repo_root / args.output_dir, force=args.force)
    server = RepoPeekMCPServer(repo_root, graph, storage, telemetry)

    if args.serve_mcp or args.serve_http:
        if args.serve_http or args.transport == "http":
            server.run_http_server(host=args.host, port=args.port, api_key=args.api_key)
        else:
            server.run_stdio_server()
        return 0

    if args.prs:
        changed_files = get_git_changed_files(repo_root, base_branch=args.base)
        impact = analyze_pr_impact(graph, changed_files)
        print(format_pr_dashboard(impact))
        return 0

    if args.watch:
        print(f"Starting incremental watch daemon for {repo_root}...")
        watcher = IncrementalWatcher(repo_root, graph, storage=storage)
        watcher.run_loop(poll_interval=0.1)
        return 0

    if args.path:
        print(server.tool_path(args.path[0], args.path[1]))
        return 0

    if args.explain:
        print(server.tool_explain(args.explain))
        return 0

    if args.query:
        print(server.tool_query(args.query, mode=args.mode))
        return 0

    if args.diagnose:
        print(server.tool_diagnose())
        return 0

    if args.cycles:
        print(server.tool_cycles())
        return 0

    if args.lookup:
        print(server.tool_lookup(args.lookup))
        return 0

    if args.neighbors:
        print(server.tool_neighbors(args.neighbors))
        return 0

    if args.impact:
        print(server.tool_impact(args.impact, max_depth=args.depth))
        return 0

    if args.trace:
        print(server.tool_data_trace(args.trace))
        return 0

    if args.context:
        print(server.tool_context(args.context, level=args.level))
        return 0

    if args.plan:
        print(server.tool_plan(args.plan))
        return 0

    if args.routes:
        print(server.tool_routes())
        return 0

    if args.co_changes:
        print(server.tool_co_changes(args.co_changes))
        return 0

    if args.savings:
        summary = telemetry.get_summary(timeframe="all_time")
        print(telemetry.render_hud_markdown(summary))
        return 0

    if args.view or args.serve:
        out_dir = repo_root / args.output_dir if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
        out_html = out_dir / "repopeek_graph.html"
        if args.view or not out_html.exists():
            summary = telemetry.get_summary(timeframe="all_time")
            export_interactive_html(graph, out_html, telemetry_summary=summary)
            print(f"Interactive graph viewer exported to {out_html}")
        if args.serve:
            import http.server
            import socketserver

            port = args.port
            directory = str(out_html.parent.resolve())
            filename = out_html.name

            class Handler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *a, **kw):
                    super().__init__(*a, directory=directory, **kw)

                def do_GET(self):
                    if self.path in ("/", ""):
                        self.path = f"/{filename}"
                    return super().do_GET()

                def log_message(self, format, *args):
                    pass

            print(f"Serving interactive graph at http://127.0.0.1:{port}/{filename}")
            try:
                with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
                    httpd.serve_forever()
            except KeyboardInterrupt:
                pass
        return 0

    if args.export_obsidian:
        vault = export_obsidian_vault(graph, args.export_obsidian)
        print(f"Obsidian vault successfully exported to {vault}")
        return 0

    if args.export_callflow:
        res = export_callflow_html(graph, args.export_callflow)
        print(f"Mermaid callflow HTML exported to {res}")
        return 0

    if args.export_wiki:
        res = export_markdown_wiki(graph, args.export_wiki)
        print(f"Agent-crawlable markdown wiki exported to {res}")
        return 0

    if args.export_cypher:
        res = export_cypher(graph, args.export_cypher)
        print(f"Cypher DDL/upserts exported to {res}")
        return 0

    if args.export_graphml:
        res = export_graphml(graph, args.export_graphml)
        print(f"GraphML exported to {res}")
        return 0

    if args.export_canvas:
        res = export_canvas(graph, args.export_canvas)
        print(f"Obsidian canvas exported to {res}")
        return 0

    if args.export_svg:
        res = export_svg(graph, args.export_svg)
        print(f"SVG diagram exported to {res}")
        return 0

    print(f"Indexed repository {repo_root}: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
