"""Graph integrity diagnostics, health checking, and anomaly reporting."""
from __future__ import annotations

from typing import Any

import networkx as nx


def diagnose_graph(
    graph: nx.DiGraph,
    records_edges: list[dict[str, Any]] | None = None,
    records_nodes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Runs a non-destructive audit gate on the code property graph."""
    total_nodes = graph.number_of_nodes()
    total_edges = graph.number_of_edges()

    self_loops: list[tuple[str, str]] = []
    for u, v in graph.edges():
        if u == v:
            self_loops.append((u, v))

    isolated_nodes: list[str] = [n for n in graph.nodes() if graph.degree(n) == 0]

    empty_locations: list[str] = []
    for n, d in graph.nodes(data=True):
        if not d.get("file_path") or d.get("start_line", 0) <= 0:
            empty_locations.append(n)

    dangling_sources: list[str] = []
    dangling_targets: list[str] = []

    if records_edges is not None:
        node_ids = set(graph.nodes())
        for e in records_edges:
            src = e.get("source", "")
            tgt = e.get("target", "")
            if src not in node_ids:
                dangling_sources.append(src)
            if tgt not in node_ids:
                dangling_targets.append(tgt)

    is_healthy = (
        len(self_loops) == 0
        and len(dangling_sources) == 0
        and len(dangling_targets) == 0
        and total_nodes > 0
    )

    return {
        "is_healthy": is_healthy,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "self_loop_edges_count": len(self_loops),
        "self_loops": self_loops[:10],
        "isolated_nodes_count": len(isolated_nodes),
        "isolated_nodes": isolated_nodes[:10],
        "empty_location_nodes_count": len(empty_locations),
        "empty_locations": empty_locations[:10],
        "dangling_sources_count": len(dangling_sources),
        "dangling_targets_count": len(dangling_targets),
    }


def format_diagnostic_report(diag: dict[str, Any]) -> str:
    """Renders a clean markdown health report of graph diagnostics."""
    status_str = "HEALTHY (Integrity Verified)" if diag["is_healthy"] else "ATTENTION NEEDED (Integrity Warnings)"

    lines = [
        "## RepoPeek Graph Diagnostics Report",
        f"Status: **{status_str}**",
        "",
        "### Graph Size:",
        f"- Total Nodes: {diag['total_nodes']:,}",
        f"- Total Edges: {diag['total_edges']:,}",
        "",
        "### Integrity Checks:",
        f"- Self-Loop Edges: {diag['self_loop_edges_count']}",
        f"- Isolated Nodes: {diag['isolated_nodes_count']}",
        f"- Nodes Without Source Location: {diag['empty_location_nodes_count']}",
        f"- Dangling Edge Sources: {diag['dangling_sources_count']}",
        f"- Dangling Edge Targets: {diag['dangling_targets_count']}",
    ]

    if diag["self_loops"]:
        lines.append("\nSample Self-Loops:")
        for u, v in diag["self_loops"][:5]:
            lines.append(f"  - `{u}` -> `{v}`")

    if diag["isolated_nodes"]:
        lines.append("\nSample Isolated Nodes:")
        for n in diag["isolated_nodes"][:5]:
            lines.append(f"  - `{n}`")

    return "\n".join(lines)
