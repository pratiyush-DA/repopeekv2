"""Graph structural analysis, cyclic dependency detection, graph diffing, and god node detection."""
from __future__ import annotations

from typing import Any

import networkx as nx


def find_import_cycles(
    graph: nx.DiGraph,
    relation_types: set[str] | None = None,
    max_cycles: int = 50,
) -> list[list[str]]:
    """Detects circular import and dependency cycles across the graph."""
    rels = relation_types or {"IMPORTS", "DEPENDS_ON", "CALLS"}

    cycle_subgraph = nx.DiGraph()
    for u, v, edata in graph.edges(data=True):
        rel = edata.get("relation", "DEPENDS_ON").upper()
        if rel in rels:
            cycle_subgraph.add_edge(u, v)

    cycles: list[list[str]] = []
    try:
        for c in nx.simple_cycles(cycle_subgraph):
            if len(c) > 1:
                cycles.append(c)
                if len(cycles) >= max_cycles:
                    break
    except Exception:
        # Fallback to strongly connected components
        for scc in nx.strongly_connected_components(cycle_subgraph):
            if len(scc) > 1:
                cycles.append(sorted(list(scc)))
                if len(cycles) >= max_cycles:
                    break

    return cycles


def graph_diff(old_graph: nx.DiGraph, new_graph: nx.DiGraph) -> dict[str, Any]:
    """Computes architectural diff between two graph versions."""
    old_nodes = set(old_graph.nodes())
    new_nodes = set(new_graph.nodes())

    added_nodes = list(new_nodes - old_nodes)
    removed_nodes = list(old_nodes - new_nodes)

    common_nodes = old_nodes & new_nodes
    modified_nodes: list[dict[str, Any]] = []

    for n in common_nodes:
        old_data = old_graph.nodes[n]
        new_data = new_graph.nodes[n]
        changes: dict[str, tuple[Any, Any]] = {}
        for k in set(old_data) | set(new_data):
            if old_data.get(k) != new_data.get(k):
                changes[k] = (old_data.get(k), new_data.get(k))
        if changes:
            modified_nodes.append({"id": n, "changes": changes})

    old_edges = set(old_graph.edges())
    new_edges = set(new_graph.edges())

    added_edges = [{"source": u, "target": v} for u, v in (new_edges - old_edges)]
    removed_edges = [{"source": u, "target": v} for u, v in (old_edges - new_edges)]

    return {
        "added_nodes_count": len(added_nodes),
        "removed_nodes_count": len(removed_nodes),
        "modified_nodes_count": len(modified_nodes),
        "added_edges_count": len(added_edges),
        "removed_edges_count": len(removed_edges),
        "added_nodes": added_nodes[:20],
        "removed_nodes": removed_nodes[:20],
        "added_edges": added_edges[:20],
        "removed_edges": removed_edges[:20],
    }


def god_nodes(graph: nx.DiGraph, top_n: int = 5) -> list[dict[str, Any]]:
    """Identifies top architectural hub nodes (god nodes) with highest connectivity."""
    scored_nodes: list[dict[str, Any]] = []

    for n, d in graph.nodes(data=True):
        in_deg = graph.in_degree(n)
        out_deg = graph.out_degree(n)
        total_deg = in_deg + out_deg

        scored_nodes.append({
            "id": n,
            "label": d.get("label", n),
            "kind": d.get("kind", "symbol"),
            "file_path": d.get("file_path", ""),
            "total_degree": total_deg,
            "in_degree": in_deg,
            "out_degree": out_deg,
            "community": d.get("community", 0),
        })

    scored_nodes.sort(key=lambda x: x["total_degree"], reverse=True)
    return scored_nodes[:top_n]


def surprising_connections(graph: nx.DiGraph, top_n: int = 5) -> list[dict[str, Any]]:
    """Identifies unexpected edges that cross distinct community boundaries."""
    surprises: list[dict[str, Any]] = []

    for u, v, edata in graph.edges(data=True):
        u_comm = graph.nodes[u].get("community", 0)
        v_comm = graph.nodes[v].get("community", 0)

        if u_comm != v_comm:
            surprises.append({
                "source": u,
                "source_label": graph.nodes[u].get("label", u),
                "source_community": u_comm,
                "target": v,
                "target_label": graph.nodes[v].get("label", v),
                "target_community": v_comm,
                "relation": edata.get("relation", "DEPENDS_ON"),
                "confidence": edata.get("confidence", 1.0),
            })

    return surprises[:top_n]


def shrink_guard(
    existing_node_count: int,
    new_node_count: int,
    force: bool = False,
) -> tuple[bool, str]:
    """Guards against accidental deletion of nodes (#479 integrity shrink guard)."""
    if existing_node_count > 0 and new_node_count < existing_node_count:
        if not force:
            return (
                False,
                f"Refusing to overwrite graph: existing graph has {existing_node_count} nodes, "
                f"but new build only has {new_node_count} nodes. Pass --force to bypass this shrink guard.",
            )
    return True, "Shrink guard passed."
