"""Unit tests for graph building, universal namespace isolation, 9 lenses, and clustering in Phase 2."""
import networkx as nx
import pytest

from repopeek.build import build_graph
from repopeek.cluster import assign_community_attributes, detect_communities
from repopeek.lenses import ALL_LENSES, get_lens_summary, project_lens
from repopeek.models import EdgeRecord, NodeRecord


def test_graph_assembly():
    n1 = NodeRecord(
        id="py:parser.py::parse",
        kind="function",
        label="parse",
        file_path="parser.py",
        start_line=10,
        end_line=25,
        lenses={"Symbol", "Call"}
    )
    n2 = NodeRecord(
        id="sql:schema.sql::table.orders",
        kind="table",
        label="orders",
        file_path="schema.sql",
        start_line=1,
        end_line=5,
        lenses={"Entity"}
    )
    e1 = EdgeRecord(
        source="py:parser.py::parse",
        target="sql:schema.sql::table.orders",
        relation="WRITES",
        confidence=1.0,
        lenses={"Data"}
    )

    G = build_graph([n1, n2], [e1])
    assert len(G.nodes) == 2
    assert len(G.edges) == 1
    assert G.has_edge("py:parser.py::parse", "sql:schema.sql::table.orders")
    assert G.nodes["py:parser.py::parse"]["start_line"] == 10
    assert G.nodes["sql:schema.sql::table.orders"]["kind"] == "table"


def test_external_stub_synthesis():
    n1 = NodeRecord(
        id="py:app.py::main",
        kind="function",
        label="main",
        file_path="app.py",
        start_line=1,
        end_line=10,
        lenses={"Symbol"}
    )
    e1 = EdgeRecord(
        source="py:app.py::main",
        target="npm:axios",
        relation="CALLS",
        confidence=0.75,
        lenses={"Call"}
    )

    G = build_graph([n1], [e1])
    assert "npm:axios" in G
    assert G.nodes["npm:axios"]["external"] is True
    assert G.nodes["npm:axios"]["kind"] == "external_stub"


def test_universal_namespace_isolation():
    # Identical symbol name 'next' across Python, TypeScript, and SQL
    n_py = NodeRecord(id="py:worker.py::next", kind="function", label="next", file_path="worker.py", start_line=1, end_line=5)
    n_ts = NodeRecord(id="ts:router.ts::next", kind="function", label="next", file_path="router.ts", start_line=1, end_line=5)
    n_sql = NodeRecord(id="sql:seq.sql::next", kind="function", label="next", file_path="seq.sql", start_line=1, end_line=5)

    G = build_graph([n_py, n_ts, n_sql], [])
    # Must remain 3 distinct nodes due to universal namespace prefixes
    assert len(G.nodes) == 3
    assert "py:worker.py::next" in G
    assert "ts:router.ts::next" in G
    assert "sql:seq.sql::next" in G


def test_materialized_9_lenses():
    G = nx.DiGraph()
    G.add_node("n_mod", lenses={"Module"})
    G.add_node("n_sym", lenses={"Symbol", "Call", "Process"})
    G.add_node("n_call", lenses={"Call"})
    G.add_node("n_class", lenses={"Class"})
    G.add_node("n_data", lenses={"Data"})
    G.add_node("n_ent", lenses={"Entity"})
    G.add_node("n_cfg", lenses={"Config"})
    G.add_node("n_proc", lenses={"Process"})
    G.add_node("n_exc", lenses={"Exception"})

    G.add_edge("n_call", "n_sym", relation="CALLS", lenses={"Call"})
    G.add_edge("n_proc", "n_sym", relation="EXECUTES", lenses={"Process"})

    for lens in ALL_LENSES:
        sub = project_lens(G, lens)
        assert len(sub.nodes) >= 1
        for _, d in sub.nodes(data=True):
            assert lens in d["lenses"]

    call_sub = project_lens(G, "Call")
    assert call_sub.has_edge("n_call", "n_sym")
    assert not call_sub.has_edge("n_proc", "n_sym")


def test_community_clustering():
    G = nx.DiGraph()
    # Cluster A: Authentication
    G.add_edge("py:auth::login", "py:auth::validate")
    G.add_edge("py:auth::login", "py:auth::hash")
    # Cluster B: Billing
    G.add_edge("py:billing::invoice", "py:billing::tax")
    G.add_edge("py:billing::invoice", "py:billing::discount")

    labels = assign_community_attributes(G)
    assert len(labels) == 2
    assert G.nodes["py:auth::login"]["community_id"] != G.nodes["py:billing::invoice"]["community_id"]
    assert "community_" in G.nodes["py:auth::login"]["community_label"]
