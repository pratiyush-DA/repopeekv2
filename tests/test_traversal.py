"""Unit tests for graph traversal, shortest path, explanation, and query."""
import networkx as nx
import pytest

from repopeek.traversal import find_shortest_path, explain_node, query_graph, resolve_node_id


@pytest.fixture
def sample_graph():
    G = nx.DiGraph()
    G.add_node(
        "py:auth.py::login",
        label="login",
        kind="function",
        file_path="auth.py",
        start_line=10,
        end_line=25,
        community=1,
        reads=["session_token"],
        writes=["user_session"],
        raises=["AuthError"],
    )
    G.add_node(
        "py:db.py::query_user",
        label="query_user",
        kind="function",
        file_path="db.py",
        start_line=50,
        end_line=70,
        community=1,
        reads=["users_table"],
        writes=[],
        raises=["DBConnectionError"],
    )
    G.add_node(
        "sql:users",
        label="users",
        kind="table",
        file_path="schema.sql",
        start_line=1,
        end_line=20,
        community=2,
    )

    G.add_edge("py:auth.py::login", "py:db.py::query_user", relation="CALLS", confidence=0.95)
    G.add_edge("py:db.py::query_user", "sql:users", relation="READS", confidence=1.0)
    return G


def test_resolve_node_id(sample_graph):
    assert resolve_node_id(sample_graph, "login") == "py:auth.py::login"
    assert resolve_node_id(sample_graph, "query_user") == "py:db.py::query_user"
    assert resolve_node_id(sample_graph, "users") == "sql:users"
    assert resolve_node_id(sample_graph, "py:auth.py::login") == "py:auth.py::login"
    assert resolve_node_id(sample_graph, "nonexistent") is None


def test_find_shortest_path_success(sample_graph):
    res = find_shortest_path(sample_graph, "login", "users")
    assert res["found"] is True
    assert res["hops_count"] == 2
    assert len(res["path_nodes"]) == 3
    assert "login" in res["formatted_text"]
    assert "users" in res["formatted_text"]


def test_find_shortest_path_not_found(sample_graph):
    sample_graph.add_node("py:isolated.py::foo", label="foo")
    res = find_shortest_path(sample_graph, "login", "foo")
    assert res["found"] is False
    assert "No path found" in res["error"]


def test_explain_node(sample_graph):
    res = explain_node(sample_graph, "login")
    assert res["found"] is True
    assert res["label"] == "login"
    assert res["kind"] == "function"
    assert res["in_degree"] == 0
    assert res["out_degree"] == 1
    assert "session_token" in res["reads"]
    assert "user_session" in res["writes"]
    assert "AuthError" in res["raises"]
    assert "query_user [CALLS]" in res["formatted_text"]


def test_query_graph(sample_graph):
    res = query_graph(sample_graph, "How does user login query database?")
    assert len(res["nodes"]) > 0
    assert "login" in res["formatted_text"]
    assert res["edges_count"] >= 1
