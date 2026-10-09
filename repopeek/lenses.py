"""9 Deterministic Materialized Lenses for on-demand architectural sub-projections."""
from __future__ import annotations

import networkx as nx
from typing import Any

ALL_LENSES = (
    "Module",
    "Symbol",
    "Call",
    "Class",
    "Data",
    "Entity",
    "Config",
    "Process",
    "Exception",
)


def project_lens(graph: nx.DiGraph, lens_name: str) -> nx.DiGraph:
    """Extracts an on-demand sub-projection containing only nodes and edges tagged with the target lens."""
    if lens_name not in ALL_LENSES:
        raise ValueError(f"Unknown lens '{lens_name}'. Valid lenses: {', '.join(ALL_LENSES)}")

    matching_nodes = [
        n for n, d in graph.nodes(data=True)
        if lens_name in d.get("lenses", set())
    ]
    sub = graph.subgraph(matching_nodes).copy()

    edges_to_remove = [
        (u, v) for u, v, d in sub.edges(data=True)
        if lens_name not in d.get("lenses", set())
    ]
    sub.remove_edges_from(edges_to_remove)
    return sub


def get_lens_summary(graph: nx.DiGraph) -> dict[str, dict[str, int]]:
    """Returns node and edge metrics for all 9 materialized lenses."""
    summary = {}
    for lens in ALL_LENSES:
        nodes_count = sum(1 for _, d in graph.nodes(data=True) if lens in d.get("lenses", set()))
        edges_count = sum(1 for _, _, d in graph.edges(data=True) if lens in d.get("lenses", set()))
        summary[lens] = {"nodes": nodes_count, "edges": edges_count}
    return summary


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    G = nx.DiGraph()
    G.add_node("py:fn", lenses={"Symbol", "Call"})
    G.add_node("sql:table", lenses={"Entity"})
    G.add_edge("py:fn", "sql:table", relation="READS", lenses={"Data"})

    call_g = project_lens(G, "Call")
    assert "py:fn" in call_g
    assert "sql:table" not in call_g

    entity_g = project_lens(G, "Entity")
    assert "sql:table" in entity_g
    assert "py:fn" not in entity_g

    summary = get_lens_summary(G)
    assert summary["Call"]["nodes"] == 1
    assert summary["Entity"]["nodes"] == 1
    print("repopeek.lenses self-test passed!")
