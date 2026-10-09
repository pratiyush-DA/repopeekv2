"""Unit tests for HTML and Obsidian graph exporters."""
from __future__ import annotations

import tempfile
from pathlib import Path
import networkx as nx
import pytest

from repopeek.exporters import export_interactive_html, export_obsidian_vault


def test_export_interactive_html():
    with tempfile.TemporaryDirectory() as tmp_dir:
        G = nx.DiGraph()
        G.add_node("py:main.py::entry", label="entry", kind="function", file_path="main.py", lenses={"Symbol", "Call"})
        G.add_node("py:util.py::helper", label="helper", kind="function", file_path="util.py", lenses={"Symbol", "Call"})
        G.add_edge("py:main.py::entry", "py:util.py::helper", relation="CALLS", lenses={"Call"})

        html_out = Path(tmp_dir) / "output.html"
        res = export_interactive_html(G, html_out)
        assert res.exists()
        text = res.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in text
        assert "RepoPeek V2" in text
        assert "entry" in text
        assert "helper" in text
        assert "d3.forceSimulation" in text


def test_export_obsidian_vault():
    with tempfile.TemporaryDirectory() as tmp_dir:
        G = nx.DiGraph()
        G.add_node("py:app.py::run", label="run", kind="function", file_path="app.py", lenses={"Symbol"})
        G.add_node("sql:db.sql::table.users", label="users", kind="table", file_path="db.sql", lenses={"Entity"})
        G.add_edge("py:app.py::run", "sql:db.sql::table.users", relation="READS")

        vault_dir = Path(tmp_dir) / "test_vault"
        res = export_obsidian_vault(G, vault_dir)
        assert res.exists()
        assert (res / ".obsidian" / "graph.json").exists()
        assert (res / "00_Overview" / "00_RepoPeek_Index.md").exists()
        assert (res / "Symbols").is_dir()

        # Check symbol note contents
        notes = list((res / "Symbols").glob("*.md"))
        assert len(notes) >= 1
        note_text = notes[0].read_text(encoding="utf-8")
        assert "---" in note_text
        assert "lenses:" in note_text
