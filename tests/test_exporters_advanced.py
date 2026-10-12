"""Unit tests for Callflow Mermaid HTML, Markdown Wiki, and GraphDB exporters."""
import tempfile
from pathlib import Path
import networkx as nx
import pytest

from repopeek.exporters import (
    export_callflow_html,
    export_canvas,
    export_cypher,
    export_graphml,
    export_markdown_wiki,
    export_svg,
)


@pytest.fixture
def sample_graph():
    G = nx.DiGraph()
    G.add_node("py:app.py::main", label="main", kind="function", file_path="app.py", start_line=1, end_line=10, community=1)
    G.add_node("py:api.py::fetch", label="fetch", kind="function", file_path="api.py", start_line=12, end_line=30, community=1)
    G.add_node("sql:db::users", label="users", kind="table", file_path="db.sql", start_line=1, end_line=10, community=2)

    G.add_edge("py:app.py::main", "py:api.py::fetch", relation="CALLS", confidence=1.0)
    G.add_edge("py:api.py::fetch", "sql:db::users", relation="READS", confidence=0.9)
    return G


def test_export_callflow_html(sample_graph):
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "callflow.html"
        res = export_callflow_html(sample_graph, out_file)
        assert res.exists()
        content = res.read_text(encoding="utf-8")
        assert "mermaid" in content
        assert "main" in content
        assert "fetch" in content
        assert "users" in content


def test_export_markdown_wiki(sample_graph):
    with tempfile.TemporaryDirectory() as tmp_dir:
        wiki_dir = Path(tmp_dir) / "wiki"
        res = export_markdown_wiki(sample_graph, wiki_dir)
        assert res.exists()
        index_file = res / "index.md"
        assert index_file.exists()
        index_content = index_file.read_text(encoding="utf-8")
        assert "Architectural Communities" in index_content

        # Check community articles exist
        articles = list(res.glob("community_*.md"))
        assert len(articles) >= 1
        comm_content = articles[0].read_text(encoding="utf-8")
        assert "Core Member Symbols" in comm_content


def test_export_cypher(sample_graph):
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "cypher.txt"
        res = export_cypher(sample_graph, out_file)
        assert res.exists()
        content = res.read_text(encoding="utf-8")
        assert "CREATE INDEX" in content
        assert "MERGE (n:Function" in content or "MERGE (n:Symbol" in content
        assert "CALLS" in content


def test_export_graphml(sample_graph):
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "graph.graphml"
        res = export_graphml(sample_graph, out_file)
        assert res.exists()
        content = res.read_text(encoding="utf-8")
        assert "<graphml" in content
        assert "app.py" in content


def test_export_canvas(sample_graph):
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "graph.canvas"
        res = export_canvas(sample_graph, out_file)
        assert res.exists()
        content = res.read_text(encoding="utf-8")
        assert '"nodes":' in content
        assert '"edges":' in content


def test_export_svg(sample_graph):
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "graph.svg"
        res = export_svg(sample_graph, out_file)
        assert res.exists()
        content = res.read_text(encoding="utf-8")
        assert "<svg" in content
        assert "</svg>" in content
