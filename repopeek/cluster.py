"""Community detection engine using Leiden clustering with deterministic Louvain/modularity fallback."""
from __future__ import annotations

import networkx as nx
from typing import Any


def detect_communities(graph: nx.DiGraph) -> dict[int, list[str]]:
    """Partitions graph into communities using Louvain / Leiden modularity optimization."""
    if len(graph) == 0:
        return {}

    # Convert DiGraph to undirected for modularity clustering
    undirected = graph.to_undirected()

    try:
        from networkx.algorithms.community import louvain_communities
        communities_raw = louvain_communities(undirected, seed=42)
    except Exception:
        from networkx.algorithms.community import greedy_modularity_communities
        communities_raw = list(greedy_modularity_communities(undirected))

    communities: dict[int, list[str]] = {}
    for idx, c_set in enumerate(communities_raw):
        # Sort members deterministically
        communities[idx] = sorted(list(c_set))

    return communities


def assign_community_attributes(graph: nx.DiGraph) -> dict[int, str]:
    """Assigns community IDs and deterministic symbol-derived labels to graph nodes.
    
    Returns a mapping of community_id -> community_label.
    """
    communities = detect_communities(graph)
    labels: dict[int, str] = {}

    for c_id, members in communities.items():
        # Find highest-degree internal node to name community deterministically
        best_node = None
        best_degree = -1
        for m in members:
            deg = graph.degree(m)
            if deg > best_degree:
                best_degree = deg
                best_node = m

        if best_node:
            stem = best_node.split("::")[-1].split(":")[-1]
            label = f"community_{stem}"
        else:
            label = f"community_{c_id}"

        labels[c_id] = label

        for m in members:
            graph.nodes[m]["community_id"] = c_id
            graph.nodes[m]["community_label"] = label

    return labels


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    G = nx.DiGraph()
    G.add_edge("py:auth::login", "py:auth::verify_token")
    G.add_edge("py:auth::login", "py:auth::hash_pwd")
    G.add_edge("py:billing::invoice", "py:billing::calculate_tax")

    labels = assign_community_attributes(G)
    assert len(labels) >= 2, "Expected at least 2 disconnected communities"
    assert "community_id" in G.nodes["py:auth::login"]
    assert "community_label" in G.nodes["py:auth::login"]
    print("repopeek.cluster self-test passed!")
