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
from repopeek.exporters.html import export_interactive_html
from repopeek.exporters.obsidian import export_obsidian_vault
from repopeek.extract import extract_file
from repopeek.models import EdgeRecord, NodeRecord
from repopeek.serve import RepoPeekMCPServer
from repopeek.storage import DualStorageEngine
from repopeek.telemetry import TelemetryTracker
from repopeek.temporal import apply_co_change_edges, mine_git_co_changes
from repopeek.watch import IncrementalWatcher


def index_repository(repo_path: Path | str, repopeek_dir: Path | str | None = None) -> tuple[nx.DiGraph, DualStorageEngine, TelemetryTracker]:
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
    storage.sync_graph(graph)

    return graph, storage, telemetry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RepoPeek V2 - Semantic Code Property Graph Engine")
    parser.add_argument("--repo-path", default=".", help="Path to target repository root (default: current directory)")
    parser.add_argument("--output-dir", default=".repopeek", help="Directory for storage and graph cache")
    parser.add_argument("--offline", action="store_true", help="Run deterministic offline indexing (zero LLM)")
    parser.add_argument("--watch", action="store_true", help="Start incremental watch daemon (<50ms sync on changes)")
    parser.add_argument("--serve-mcp", action="store_true", help="Start stdio JSON-RPC Model Context Protocol server")

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

    # Exporters & Viewers
    parser.add_argument("--view", action="store_true", help="Generate standalone interactive D3 HTML graph viewer")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve interactive web viewer")
    parser.add_argument("--export-obsidian", help="Export graph into an Obsidian Markdown vault")

    args = parser.parse_args(argv)
    repo_root = Path(args.repo_path).resolve()

    # Fast path: savings without re-indexing full repo if ledger exists
    if args.savings and not (args.lookup or args.impact or args.trace or args.context or args.plan):
        telemetry = TelemetryTracker(repopeek_dir=repo_root / args.output_dir)
        summary = telemetry.get_summary(timeframe="all_time")
        print(telemetry.render_hud_markdown(summary))
        return 0

    # Index repository
    graph, storage, telemetry = index_repository(repo_root, repopeek_dir=repo_root / args.output_dir)
    server = RepoPeekMCPServer(repo_root, graph, storage, telemetry)

    if args.serve_mcp:
        server.run_stdio_server()
        return 0

    if args.watch:
        print(f"Starting incremental watch daemon for {repo_root}...")
        watcher = IncrementalWatcher(repo_root, graph, storage=storage)
        watcher.run_loop(poll_interval=0.1)
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

    if args.view:
        out_html = Path(args.output_dir) / "repopeek_graph.html"
        summary = telemetry.get_summary(timeframe="all_time")
        export_interactive_html(graph, out_html, telemetry_summary=summary)
        print(f"Interactive graph viewer exported to {out_html}")
        return 0

    if args.export_obsidian:
        vault = export_obsidian_vault(graph, args.export_obsidian)
        print(f"Obsidian vault successfully exported to {vault}")
        return 0

    print(f"Indexed repository {repo_root}: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
