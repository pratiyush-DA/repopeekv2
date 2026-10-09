"""Cross-Language HTTP Boundary Bridge connecting client API calls to backend route handlers."""
from __future__ import annotations

import re
import networkx as nx
from typing import Any

from repopeek.models import EdgeRecord

_PARAM_SUB_RE = re.compile(r"\{[a-zA-Z0-9_]+\}|<[a-zA-Z0-9_:]+>|:[a-zA-Z0-9_]+")
_TRAILING_SLASH_RE = re.compile(r"/+$")
_MULTIPLE_SLASHES_RE = re.compile(r"/+")


def normalize_endpoint_path(path: str) -> str:
    """Normalizes route patterns into canonical form with wildcard :param tokens.
    
    Examples:
    - /api/v1/invoices/{invoice_id} -> /api/v1/invoices/:param
    - /api/v1/invoices/:id/ -> /api/v1/invoices/:param
    - /items/<int:item_id> -> /items/:param
    """
    if not path:
        return ""
    # Strip URL query params if any
    p = path.split("?")[0].strip()
    # Normalize multiple slashes to single slash
    p = _MULTIPLE_SLASHES_RE.sub("/", p)
    # Replace variable parameter tokens with :param
    p = _PARAM_SUB_RE.sub(":param", p)
    # Strip trailing slash unless root
    if len(p) > 1:
        p = _TRAILING_SLASH_RE.sub("", p)
    return p


def synthesize_http_bridges(graph: nx.DiGraph) -> list[EdgeRecord]:
    """Finds client API call endpoints and server route handlers, synthesizing INVOKES edges."""
    server_routes: dict[str, list[str]] = {}  # normalized_path -> list of server node_ids
    client_calls: list[tuple[str, str]] = []  # (client_node_id, raw_url)

    for node_id, data in graph.nodes(data=True):
        kind = data.get("kind", "")
        label = data.get("label", "")
        meta = data.get("metadata", {})

        # Check if node is a server route endpoint
        route_path = meta.get("route_path") or meta.get("endpoint")
        if not route_path and ("route" in kind or "endpoint" in kind or "@router." in label or "@app." in label):
            # Attempt to extract path from label or docstring
            m = re.search(r'["\'](/[^"\']+)["\']', label)
            if m:
                route_path = m.group(1)

        if route_path:
            norm = normalize_endpoint_path(route_path)
            if norm:
                server_routes.setdefault(norm, []).append(node_id)

        # Check if node makes a client API call
        client_target = meta.get("api_call") or meta.get("url")
        if not client_target:
            # Check docstring or metadata for fetch/axios patterns
            for field in ("docstring", "evidence"):
                text = data.get(field, "")
                m = re.search(r'(?:fetch|axios(?:\.[a-z]+)?|http(?:\.[a-z]+)?)\s*\(\s*["\'](/[^"\']+)["\']', text)
                if m:
                    client_target = m.group(1)
                    break

        if client_target:
            client_calls.append((node_id, client_target))

    bridges: list[EdgeRecord] = []
    for client_node, raw_url in client_calls:
        norm_call = normalize_endpoint_path(raw_url)
        matching_servers = server_routes.get(norm_call, [])
        for server_node in matching_servers:
            edge = EdgeRecord(
                source=client_node,
                target=server_node,
                relation="INVOKES",
                confidence=0.75,
                lenses={"Call"},
                evidence=f"HTTP boundary bridge: {raw_url} -> {server_node}"
            )
            bridges.append(edge)
            graph.add_edge(
                client_node,
                server_node,
                relation="INVOKES",
                confidence=0.75,
                lenses={"Call"},
                evidence=edge.evidence,
                metadata={}
            )

    return bridges


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    assert normalize_endpoint_path("/api/v1/users/{id}/") == "/api/v1/users/:param"
    assert normalize_endpoint_path("/items/<int:itemId>") == "/items/:param"
    assert normalize_endpoint_path("/orders/:order_id") == "/orders/:param"

    G = nx.DiGraph()
    G.add_node("ts:client.ts::fetchInvoices", kind="function", metadata={"api_call": "/api/v1/invoices/:id"})
    G.add_node("py:server.py::get_invoice", kind="route", metadata={"route_path": "/api/v1/invoices/{invoice_id}"})

    synthesized = synthesize_http_bridges(G)
    assert len(synthesized) == 1, "Expected 1 synthesized HTTP boundary bridge"
    assert synthesized[0].relation == "INVOKES"
    assert G.has_edge("ts:client.ts::fetchInvoices", "py:server.py::get_invoice")
    print("repopeek.bridges.http self-test passed!")
