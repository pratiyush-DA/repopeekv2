"""Unit tests for work memory reflection and git hooks lifecycle."""
import tempfile
from pathlib import Path
import networkx as nx
import pytest

from repopeek.hooks import get_hook_status, install_hooks, uninstall_hooks
from repopeek.reflect import reflect, save_result


@pytest.fixture
def sample_graph():
    G = nx.DiGraph()
    G.add_node("py:auth.py::login", label="login", community=1)
    G.add_node("py:db.py::query", label="query", community=1)
    G.add_edge("py:auth.py::login", "py:db.py::query", relation="CALLS")
    return G


def test_save_result_and_reflect(sample_graph):
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_dir = Path(tmp_dir) / ".repopeek"
        lessons_file = Path(tmp_dir) / "docs" / "LESSONS.md"

        # Record a useful outcome citing login twice
        save_result(base_dir, "How does auth work?", "Via login function", outcome="useful", nodes=["py:auth.py::login"])
        save_result(base_dir, "Where is session checked?", "In login function", outcome="useful", nodes=["py:auth.py::login"])

        # Record a dead end
        save_result(base_dir, "Is there an LDAP module?", "No LDAP module found", outcome="dead_end", nodes=["py:db.py::query"])

        # Run reflection
        summary = reflect(base_dir, graph=sample_graph, out_markdown=lessons_file, min_corroboration=2)
        assert summary["total_memories"] == 3
        assert "py:auth.py::login" in summary["preferred_nodes"]
        assert summary["dead_ends_count"] == 1
        assert lessons_file.exists()

        content = lessons_file.read_text(encoding="utf-8")
        assert "Architectural Lessons" in content
        assert "login" in content
        assert "Avoid" in content


def test_git_hooks_lifecycle():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = Path(tmp_dir)
        # Initialize dummy .git folder
        (repo_dir / ".git" / "hooks").mkdir(parents=True)

        status_init = get_hook_status(repo_dir)
        assert status_init["post_commit"] is False

        # Install
        install_res = install_hooks(repo_dir)
        assert install_res["status"] == "success"

        status_after = get_hook_status(repo_dir)
        assert status_after["post_commit"] is True
        assert status_after["post_checkout"] is True

        # Uninstall
        uninstalled = uninstall_hooks(repo_dir)
        assert uninstalled is True

        status_final = get_hook_status(repo_dir)
        assert status_final["post_commit"] is False
