"""Unit tests for graph integrity diagnostics and health checking."""
import networkx as nx

from repopeek.diagnostics import diagnose_graph, format_diagnostic_report


def test_diagnose_healthy_graph():
    G = nx.DiGraph()
    G.add_node("py:a.py::f1", label="f1", file_path="a.py", start_line=1)
    G.add_node("py:b.py::f2", label="f2", file_path="b.py", start_line=5)
    G.add_edge("py:a.py::f1", "py:b.py::f2", relation="CALLS")

    diag = diagnose_graph(G)
    assert diag["is_healthy"] is True
    assert diag["total_nodes"] == 2
    assert diag["total_edges"] == 1
    assert diag["self_loop_edges_count"] == 0
    assert diag["isolated_nodes_count"] == 0
    assert diag["empty_location_nodes_count"] == 0

    report = format_diagnostic_report(diag)
    assert "HEALTHY" in report


def test_diagnose_unhealthy_graph():
    G = nx.DiGraph()
    G.add_node("py:a.py::loop", label="loop", file_path="a.py", start_line=1)
    G.add_node("py:isolated", label="isolated")  # Missing file_path & line
    G.add_edge("py:a.py::loop", "py:a.py::loop", relation="CALLS")  # Self loop

    raw_edges = [
        {"source": "py:a.py::loop", "target": "missing_node", "relation": "CALLS"},
    ]

    diag = diagnose_graph(G, records_edges=raw_edges)
    assert diag["is_healthy"] is False
    assert diag["self_loop_edges_count"] == 1
    assert diag["isolated_nodes_count"] == 1
    assert diag["empty_location_nodes_count"] == 1
    assert diag["dangling_targets_count"] == 1

    report = format_diagnostic_report(diag)
    assert "ATTENTION NEEDED" in report
