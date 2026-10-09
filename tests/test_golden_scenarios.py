"""Golden Scenarios 1, 2, and 3 End-to-End Integration Verification."""
from __future__ import annotations

import tempfile
from pathlib import Path
import networkx as nx
import pytest

from repopeek.bridges.http import synthesize_http_bridges
from repopeek.bridges.sql import synthesize_sql_bridges
from repopeek.build import build_graph_from_records
from repopeek.context import ContextCompiler, ChangePlanEngine
from repopeek.detect import scan_workspace
from repopeek.extract import extract_file
from repopeek.models import EdgeRecord, NodeRecord
from repopeek.serve import RepoPeekMCPServer
from repopeek.storage import DualStorageEngine
from repopeek.telemetry import TelemetryTracker


def test_golden_scenario_1_cross_language_http():
    """Golden Scenario 1: TypeScript client API call matches Python FastAPI route handler."""
    G = nx.DiGraph()
    # TypeScript API Client
    G.add_node(
        "ts:src/api/invoiceClient.ts::fetchInvoice",
        label="fetchInvoice",
        kind="function",
        file_path="src/api/invoiceClient.ts",
        start_line=12,
        end_line=25,
        metadata={"api_call": "/api/v1/invoices/:id"},
        lenses={"Symbol", "Call"}
    )
    # Python FastAPI Backend Route
    G.add_node(
        "py:backend/routes/invoices.py::get_invoice",
        label="get_invoice",
        kind="route",
        file_path="backend/routes/invoices.py",
        start_line=45,
        end_line=60,
        metadata={"route_path": "/api/v1/invoices/{invoice_id}"},
        lenses={"Symbol", "Call"}
    )

    bridges = synthesize_http_bridges(G)
    assert len(bridges) == 1
    edge = bridges[0]
    assert edge.source == "ts:src/api/invoiceClient.ts::fetchInvoice"
    assert edge.target == "py:backend/routes/invoices.py::get_invoice"
    assert edge.relation == "INVOKES"
    assert edge.confidence == 0.75
    assert "Call" in edge.lenses

    # Verify graph connectivity
    assert G.has_edge("ts:src/api/invoiceClient.ts::fetchInvoice", "py:backend/routes/invoices.py::get_invoice")


def test_golden_scenario_2_sql_def_use_and_blast_radius():
    """Golden Scenario 2: SQL DDL table binds to application mutation and query blast radius."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = DualStorageEngine(repopeek_dir=tmp_dir)
        G = nx.DiGraph()

        # SQL Table
        G.add_node(
            "sql:schema.sql::table.invoices",
            label="invoices",
            kind="table",
            file_path="schema.sql",
            start_line=1,
            end_line=15,
            lenses={"Entity"}
        )
        # Python mutation service
        G.add_node(
            "py:services/invoice_service.py::create_invoice",
            label="create_invoice",
            kind="function",
            file_path="services/invoice_service.py",
            start_line=20,
            end_line=45,
            writes=["invoices"],
            lenses={"Symbol", "Data"}
        )
        # Python reporting query
        G.add_node(
            "py:analytics/reporter.py::generate_monthly_report",
            label="generate_monthly_report",
            kind="function",
            file_path="analytics/reporter.py",
            start_line=10,
            end_line=35,
            reads=["invoices"],
            lenses={"Symbol", "Data"}
        )
        # API caller
        G.add_node(
            "py:api/routes.py::post_checkout",
            label="post_checkout",
            kind="function",
            file_path="api/routes.py",
            start_line=5,
            end_line=18,
            lenses={"Symbol", "Call"}
        )
        G.add_edge("py:api/routes.py::post_checkout", "py:services/invoice_service.py::create_invoice", relation="CALLS")

        # Synthesize SQL bridges
        sql_edges = synthesize_sql_bridges(G)
        assert len(sql_edges) == 2

        storage.sync_graph(G)

        # Blast radius analysis of table.invoices
        upstream = storage.query_upstream_blast_radius("sql:schema.sql::table.invoices", max_depth=3)
        upstream_nodes = [u["node_id"] for u in upstream]
        assert "py:services/invoice_service.py::create_invoice" in upstream_nodes
        assert "py:analytics/reporter.py::generate_monthly_report" in upstream_nodes
        assert "py:api/routes.py::post_checkout" in upstream_nodes


def test_golden_scenario_3_context_compiler_and_roi_telemetry():
    """Golden Scenario 3: Context Compiler strictly enforces <=4 files, ~40 lines, with ROI HUD."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # Create 15 modules in workspace
        G = nx.DiGraph()
        for i in range(15):
            fp = f"pkg/mod_{i}.py"
            p = root / fp
            p.parent.mkdir(parents=True, exist_ok=True)
            code_lines = [f"# header {j}" for j in range(80)]
            code_lines[30] = f"def execute_task_{i}():"
            code_lines[31] = f"    return {i}"
            p.write_text("\n".join(code_lines), encoding="utf-8")

            G.add_node(
                f"py:{fp}::execute_task_{i}",
                label=f"execute_task_{i}",
                kind="function",
                file_path=fp,
                start_line=30,
                end_line=32,
            )

        storage = DualStorageEngine(repopeek_dir=root / ".repopeek")
        storage.sync_graph(G)
        telemetry = TelemetryTracker(repopeek_dir=root / ".repopeek")

        server = RepoPeekMCPServer(root, G, storage=storage, telemetry=telemetry)

        # Execute repopeek_context
        context_output = server.dispatch_tool("repopeek_context", {"task": "Refactor execute_task_5 function"})

        assert "REPOPEEK EFFICIENCY SCORECARD" in context_output
        assert "pkg/mod_5.py" in context_output
        assert "30 |" in context_output  # focus span ~40 lines with line numbers

        # Query savings
        savings_output = server.dispatch_tool("repopeek_savings", {})
        assert "RepoPeek Context Efficiency & ROI Scoreboard" in savings_output
        assert "Total Agent Tasks Completed**: 1" in savings_output

        # Verify summary stats
        summary = telemetry.get_summary()
        assert summary["total_files_avoided"] >= 10
        assert summary["total_tokens_saved"] > 5000
        assert summary["overall_reduction_pct"] > 85.0
