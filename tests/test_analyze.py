"""Unit tests for cycle detection, graph diffing, god nodes, and shrink guard."""
import networkx as nx

from repopeek.analyze import find_import_cycles, god_nodes, graph_diff, shrink_guard, surprising_connections


def test_find_import_cycles():
    G = nx.DiGraph()
    G.add_edge("mod_a", "mod_b", relation="IMPORTS")
    G.add_edge("mod_b", "mod_c", relation="IMPORTS")
    G.add_edge("mod_c", "mod_a", relation="IMPORTS")
    G.add_edge("mod_c", "mod_d", relation="IMPORTS")

    cycles = find_import_cycles(G)
    assert len(cycles) == 1
    assert set(cycles[0]) == {"mod_a", "mod_b", "mod_c"}


def test_graph_diff():
    g1 = nx.DiGraph()
    g1.add_node("node1", label="v1")
    g1.add_node("node2", label="stable")
    g1.add_edge("node1", "node2")

    g2 = nx.DiGraph()
    g2.add_node("node2", label="stable")
    g2.add_node("node3", label="new")
    g2.add_edge("node2", "node3")

    diff = graph_diff(g1, g2)
    assert diff["added_nodes_count"] == 1
    assert "node3" in diff["added_nodes"]
    assert diff["removed_nodes_count"] == 1
    assert "node1" in diff["removed_nodes"]
    assert diff["added_edges_count"] == 1
    assert diff["removed_edges_count"] == 1


def test_god_nodes_and_surprises():
    G = nx.DiGraph()
    G.add_node("hub", label="HubNode", community=1)
    G.add_node("leaf1", label="Leaf1", community=1)
    G.add_node("leaf2", label="Leaf2", community=2)

    G.add_edge("leaf1", "hub", relation="CALLS")
    G.add_edge("hub", "leaf2", relation="CALLS")

    gods = god_nodes(G, top_n=1)
    assert len(gods) == 1
    assert gods[0]["id"] == "hub"
    assert gods[0]["total_degree"] == 2

    surprises = surprising_connections(G, top_n=5)
    assert len(surprises) == 1
    assert surprises[0]["source"] == "hub"
    assert surprises[0]["target"] == "leaf2"


def test_shrink_guard():
    # Attempting to shrink from 10 nodes to 5 without force -> blocked
    passed, msg = shrink_guard(10, 5, force=False)
    assert passed is False
    assert "Refusing to overwrite" in msg

    # With force -> allowed
    passed_forced, msg_forced = shrink_guard(10, 5, force=True)
    assert passed_forced is True

    # Growing graph -> allowed
    passed_grow, _ = shrink_guard(10, 15, force=False)
    assert passed_grow is True
