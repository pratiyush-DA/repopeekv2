"""Unit tests for 11-Tool Model Context Protocol (MCP) server."""
from __future__ import annotations

import tempfile
from pathlib import Path
import networkx as nx
import pytest

from repopeek.serve import RepoPeekMCPServer
from repopeek.storage import DualStorageEngine
from repopeek.telemetry import TelemetryTracker


@pytest.fixture
def test_server():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        p1 = root / "invoice.py"
        p1.write_text("def parse_invoice(pdf):\n    return {}\n", encoding="utf-8")

        G = nx.DiGraph()
        G.add_node("py:invoice.py::parse_invoice", label="parse_invoice", kind="function", file_path="invoice.py", start_line=1, end_line=3, writes=["invoices"])
        G.add_node("py:api.py::checkout", label="checkout", kind="function", file_path="api.py", start_line=1, end_line=5)
        G.add_node("sql:db.sql::table.invoices", label="invoices", kind="table", file_path="db.sql")
        G.add_edge("py:api.py::checkout", "py:invoice.py::parse_invoice", relation="CALLS")
        G.add_edge("py:invoice.py::parse_invoice", "sql:db.sql::table.invoices", relation="WRITES")

        storage = DualStorageEngine(repopeek_dir=root / ".repopeek")
        storage.sync_graph(G)
        telemetry = TelemetryTracker(repopeek_dir=root / ".repopeek")

        yield RepoPeekMCPServer(root, G, storage=storage, telemetry=telemetry)


def test_mcp_tool_definitions_count(test_server):
    defs = test_server.get_tool_definitions()
    assert len(defs) == 11
    names = {d["name"] for d in defs}
    expected = {
        "repopeek_lookup",
        "repopeek_neighbors",
        "repopeek_impact",
        "repopeek_data_trace",
        "repopeek_context_pack",
        "repopeek_context",
        "repopeek_plan",
        "repopeek_routes",
        "repopeek_co_changes",
        "repopeek_resolve",
        "repopeek_savings",
    }
    assert names == expected


def test_mcp_tools_execution(test_server):
    # 1. lookup
    res_lookup = test_server.dispatch_tool("repopeek_lookup", {"query": "parse_invoice"})
    assert "parse_invoice" in res_lookup

    # 2. neighbors
    res_neigh = test_server.dispatch_tool("repopeek_neighbors", {"query": "parse_invoice"})
    assert "checkout" in res_neigh
    assert "invoices" in res_neigh

    # 3. impact
    res_impact = test_server.dispatch_tool("repopeek_impact", {"target": "parse_invoice", "max_depth": 2})
    assert "checkout" in res_impact

    # 4. data_trace
    res_trace = test_server.dispatch_tool("repopeek_data_trace", {"query": "invoices"})
    assert "parse_invoice" in res_trace

    # 5. context_pack
    res_pack = test_server.dispatch_tool("repopeek_context_pack", {"targets": ["py:invoice.py::parse_invoice"]})
    assert "invoice.py" in res_pack

    # 6. context (with efficiency scorecard)
    res_context = test_server.dispatch_tool("repopeek_context", {"task": "Update parse_invoice logic"})
    assert "REPOPEEK EFFICIENCY SCORECARD" in res_context
    assert "invoice.py" in res_context

    # 7. plan
    res_plan = test_server.dispatch_tool("repopeek_plan", {"task": "Enhance invoice parser"})
    assert "# Change Plan:" in res_plan
    assert "Step 1: Pre-flight Verification" in res_plan

    # 8. routes
    res_routes = test_server.dispatch_tool("repopeek_routes", {})
    assert "Cross-Language HTTP Routes" in res_routes

    # 9. co_changes
    res_co = test_server.dispatch_tool("repopeek_co_changes", {"target": "invoice.py"})
    assert "Git Temporal Co-Changes" in res_co

    # 10. resolve
    res_resolve = test_server.dispatch_tool("repopeek_resolve", {"task": "invoice parsing"})
    assert "parse_invoice" in res_resolve

    # 11. savings
    res_savings = test_server.dispatch_tool("repopeek_savings", {})
    assert "RepoPeek Context Efficiency & ROI Scoreboard" in res_savings
