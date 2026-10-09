"""Unit tests for Phase 3 Cross-Language Bridges (HTTP and SQL)."""
from __future__ import annotations

import networkx as nx
import pytest

from repopeek.bridges.http import normalize_endpoint_path, synthesize_http_bridges
from repopeek.bridges.sql import synthesize_sql_bridges
from repopeek.bridges import apply_all_bridges


def test_normalize_endpoint_path():
    assert normalize_endpoint_path("/api/v1/users/{id}") == "/api/v1/users/:param"
    assert normalize_endpoint_path("/api/v1/users/{user_id}/") == "/api/v1/users/:param"
    assert normalize_endpoint_path("/items/<int:itemId>") == "/items/:param"
    assert normalize_endpoint_path("/orders/:order_id") == "/orders/:param"
    assert normalize_endpoint_path("/orders///details") == "/orders/details"
    assert normalize_endpoint_path("/items?filter=active") == "/items"


def test_synthesize_http_bridges():
    G = nx.DiGraph()
    # Frontend client call
    G.add_node("ts:src/api/client.ts::fetchInvoice", kind="function", metadata={"api_call": "/api/v1/invoices/:id"})
    # Backend route endpoint
    G.add_node("py:backend/routes.py::get_invoice", kind="route", metadata={"route_path": "/api/v1/invoices/{invoice_id}"})
    # Unrelated function
    G.add_node("py:backend/util.py::format_date", kind="function")

    bridges = synthesize_http_bridges(G)
    assert len(bridges) == 1
    assert bridges[0].source == "ts:src/api/client.ts::fetchInvoice"
    assert bridges[0].target == "py:backend/routes.py::get_invoice"
    assert bridges[0].relation == "INVOKES"
    assert bridges[0].confidence == 0.75
    assert "Call" in bridges[0].lenses

    # Verify edge added to graph
    assert G.has_edge("ts:src/api/client.ts::fetchInvoice", "py:backend/routes.py::get_invoice")
    assert G.edges["ts:src/api/client.ts::fetchInvoice", "py:backend/routes.py::get_invoice"]["relation"] == "INVOKES"


def test_synthesize_sql_bridges():
    G = nx.DiGraph()
    # SQL Table node
    G.add_node("sql:schema.sql::table.users", kind="table", label="users")
    G.add_node("sql:schema.sql::table.transactions", kind="table", label="transactions")

    # Backend functions with reads/writes
    G.add_node("py:services/auth.py::authenticate", kind="function", reads=["users"])
    G.add_node("py:services/ledger.py::record_tx", kind="function", reads=["users"], writes=["transactions"])

    bridges = synthesize_sql_bridges(G)
    assert len(bridges) == 3

    assert G.has_edge("py:services/auth.py::authenticate", "sql:schema.sql::table.users")
    assert G.edges["py:services/auth.py::authenticate", "sql:schema.sql::table.users"]["relation"] == "READS"

    assert G.has_edge("py:services/ledger.py::record_tx", "sql:schema.sql::table.transactions")
    assert G.edges["py:services/ledger.py::record_tx", "sql:schema.sql::table.transactions"]["relation"] == "WRITES"


def test_apply_all_bridges():
    G = nx.DiGraph()
    G.add_node("ts:client.ts::getOrders", kind="function", metadata={"api_call": "/api/orders"})
    G.add_node("py:api.py::orders_endpoint", kind="route", metadata={"route_path": "/api/orders"})
    G.add_node("sql:db.sql::table.orders", kind="table", label="orders")
    G.add_node("py:api.py::orders_endpoint", kind="route", reads=["orders"], metadata={"route_path": "/api/orders"})

    all_bridges = apply_all_bridges(G)
    assert len(all_bridges) >= 2
    relations = {b.relation for b in all_bridges}
    assert "INVOKES" in relations
    assert "READS" in relations
