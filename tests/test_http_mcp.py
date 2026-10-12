"""Unit tests for RepoPeek MCP HTTP server transport."""
import json
import threading
import time
import urllib.request
import networkx as nx
import pytest

from repopeek.serve import RepoPeekMCPServer


@pytest.fixture
def http_server():
    G = nx.DiGraph()
    G.add_node("py:test.py::main", label="main", kind="function", file_path="test.py", start_line=1, end_line=10)
    server = RepoPeekMCPServer(".", G)

    port = 8999
    host = "127.0.0.1"

    thread = threading.Thread(
        target=lambda: server.run_http_server(host=host, port=port, api_key="secret-key"),
        daemon=True,
    )
    thread.start()
    time.sleep(0.3)  # Allow server to bind socket

    yield f"http://{host}:{port}/mcp"


def test_http_get_status_authorized(http_server):
    req = urllib.request.Request(http_server, headers={"Authorization": "Bearer secret-key"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "ok"
        assert data["server"] == "repopeek"
        assert data["tools_count"] == 16


def test_http_unauthorized(http_server):
    req = urllib.request.Request(http_server, headers={"Authorization": "Bearer wrong-key"})
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 401


def test_http_tools_call(http_server):
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
        "params": {
            "name": "repopeek_lookup",
            "arguments": {"query": "main"},
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        http_server,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "secret-key",
        },
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        assert res["id"] == "1"
        assert "main" in res["result"]["content"][0]["text"]
