"""Unit tests for multi-repo global graph and PR impact/conflict analysis."""
import tempfile
from pathlib import Path
import networkx as nx
import pytest

from repopeek.global_graph import add_repo_to_global, list_global_repos, merge_graphs, remove_repo_from_global
from repopeek.prs import analyze_pr_impact, detect_branch_conflicts, format_pr_dashboard


@pytest.fixture
def sample_graph():
    G = nx.DiGraph()
    G.add_node("py:auth.py::login", label="login", file_path="auth.py", community=1)
    G.add_node("py:db.py::query", label="query", file_path="db.py", community=1)
    G.add_node("py:api.py::checkout", label="checkout", file_path="api.py", community=2)
    G.add_edge("py:api.py::checkout", "py:auth.py::login", relation="CALLS")
    G.add_edge("py:auth.py::login", "py:db.py::query", relation="CALLS")
    return G


def test_merge_graphs():
    g1 = nx.DiGraph()
    g1.add_node("n1", label="Node1", lenses={"Call"})
    g1.add_node("n2", label="Node2")
    g1.add_edge("n1", "n2", relation="CALLS")

    g2 = nx.DiGraph()
    g2.add_node("n2", label="Node2", lenses={"Data"})
    g2.add_node("n3", label="Node3")
    g2.add_edge("n2", "n3", relation="READS")

    merged = merge_graphs([g1, g2])
    assert merged.number_of_nodes() == 3
    assert merged.number_of_edges() == 2
    assert "Call" in merged.nodes["n2"]["lenses"] or "Data" in merged.nodes["n2"]["lenses"]


def test_analyze_pr_impact(sample_graph):
    # Changing auth.py modifies 'login', which is called by 'checkout'
    res = analyze_pr_impact(sample_graph, ["auth.py"])
    assert res["changed_files_count"] == 1
    assert res["modified_nodes_count"] == 1
    assert 1 in res["touched_communities"]
    assert res["external_callers_count"] == 1
    assert res["external_callers"][0]["caller_label"] == "checkout"
    assert res["risk_level"] in ("LOW", "MEDIUM", "HIGH")

    dashboard = format_pr_dashboard(res)
    assert "Pull Request Impact Analysis" in dashboard
    assert "checkout" in dashboard


def test_detect_branch_conflicts(sample_graph):
    # Branch 1 changes auth.py (Community 1)
    # Branch 2 changes db.py (Community 1) -> Overlap on Community 1
    # Branch 3 changes api.py (Community 2) -> No community overlap with auth.py
    diffs = {
        "feature/oauth": ["auth.py"],
        "refactor/database": ["db.py"],
        "feature/payments": ["api.py"],
    }

    conflicts = detect_branch_conflicts(sample_graph, diffs)
    # There should be an overlap between feature/oauth and refactor/database on community 1
    assert len(conflicts) >= 1
    c = conflicts[0]
    assert "feature/oauth" in (c["branch_a"], c["branch_b"])
    assert "refactor/database" in (c["branch_a"], c["branch_b"])
    assert 1 in c["overlapping_communities"]
