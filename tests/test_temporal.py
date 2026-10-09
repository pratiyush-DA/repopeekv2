"""Unit tests for Phase 3 Git Temporal Mining and Co-Change Matrix."""
from __future__ import annotations

from pathlib import Path
import networkx as nx
import pytest

from repopeek.temporal import apply_co_change_edges, mine_git_co_changes


def test_mine_git_co_changes_current_repo():
    # Mining the current repopeek repository
    co_changes = mine_git_co_changes(".")
    assert isinstance(co_changes, dict)


def test_apply_co_change_edges():
    G = nx.DiGraph()
    G.add_node("py:services/auth.py", file_path="services/auth.py")
    G.add_node("py:tests/test_auth.py", file_path="tests/test_auth.py")

    fake_matrix = {
        "services/auth.py": {
            "tests/test_auth.py": 0.85
        }
    }

    edges = apply_co_change_edges(G, fake_matrix)
    assert len(edges) == 1
    assert edges[0].source == "py:services/auth.py"
    assert edges[0].target == "py:tests/test_auth.py"
    assert edges[0].relation == "CO_CHANGED_WITH"
    assert edges[0].confidence == 0.85
    assert "Module" in edges[0].lenses

    assert G.has_edge("py:services/auth.py", "py:tests/test_auth.py")
    assert G.edges["py:services/auth.py", "py:tests/test_auth.py"]["confidence"] == 0.85
