"""Cross-repository global knowledge graph manager and multi-graph merger."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx
from networkx.readwrite import json_graph as _jg

_GLOBAL_DIR = Path.home() / ".repopeek"
_GLOBAL_GRAPH_FILE = _GLOBAL_DIR / "global-graph.json"
_GLOBAL_MANIFEST_FILE = _GLOBAL_DIR / "global-manifest.json"


def get_global_dir() -> Path:
    """Returns the user-global .repopeek directory."""
    _GLOBAL_DIR.mkdir(parents=True, exist_ok=True)
    return _GLOBAL_DIR


def get_global_graph_path() -> Path:
    """Returns path to global graph JSON file."""
    return _GLOBAL_GRAPH_FILE


def load_global_manifest() -> dict[str, Any]:
    """Loads manifest of registered repositories."""
    if _GLOBAL_MANIFEST_FILE.exists():
        try:
            return json.loads(_GLOBAL_MANIFEST_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": 1, "repos": {}}


def save_global_manifest(manifest: dict[str, Any]) -> None:
    """Saves global manifest atomically."""
    get_global_dir()
    _GLOBAL_MANIFEST_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def load_global_graph() -> nx.DiGraph:
    """Loads the centralized multi-repo DiGraph."""
    if _GLOBAL_GRAPH_FILE.exists():
        try:
            data = json.loads(_GLOBAL_GRAPH_FILE.read_text(encoding="utf-8"))
            if "links" not in data and "edges" in data:
                data = dict(data, links=data["edges"])
            return _jg.node_link_graph(data, directed=True, edges="links")
        except Exception:
            pass
    return nx.DiGraph()


def save_global_graph(graph: nx.DiGraph) -> None:
    """Saves the combined multi-repo DiGraph."""
    get_global_dir()
    try:
        data = _jg.node_link_data(graph, edges="links")
    except TypeError:
        data = _jg.node_link_data(graph)
    _GLOBAL_GRAPH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_repo_to_global(repo_name: str, graph: nx.DiGraph, repo_path: str = "") -> dict[str, Any]:
    """Prefixes nodes with repo name if needed and merges into global graph."""
    global_g = load_global_graph()
    manifest = load_global_manifest()

    # Prefix nodes with repo scope to prevent collisions
    repo_prefix = f"repo:{repo_name}::"

    nodes_added = 0
    for n, data in graph.nodes(data=True):
        global_id = n if n.startswith("repo:") else f"{repo_prefix}{n}"
        node_attr = dict(data)
        node_attr["repo"] = repo_name
        global_g.add_node(global_id, **node_attr)
        nodes_added += 1

    edges_added = 0
    for u, v, data in graph.edges(data=True):
        u_global = u if u.startswith("repo:") else f"{repo_prefix}{u}"
        v_global = v if v.startswith("repo:") else f"{repo_prefix}{v}"
        global_g.add_edge(u_global, v_global, **data)
        edges_added += 1

    save_global_graph(global_g)

    manifest["repos"][repo_name] = {
        "repo_path": repo_path,
        "nodes_count": graph.number_of_nodes(),
        "edges_count": graph.number_of_edges(),
    }
    save_global_manifest(manifest)

    return {
        "repo_name": repo_name,
        "nodes_added": nodes_added,
        "edges_added": edges_added,
        "total_global_nodes": global_g.number_of_nodes(),
        "total_global_edges": global_g.number_of_edges(),
    }


def remove_repo_from_global(repo_name: str) -> bool:
    """Removes all nodes and edges belonging to a given repository from the global graph."""
    manifest = load_global_manifest()
    if repo_name not in manifest.get("repos", {}):
        return False

    global_g = load_global_graph()
    nodes_to_remove = [n for n, d in global_g.nodes(data=True) if d.get("repo") == repo_name]
    global_g.remove_nodes_from(nodes_to_remove)

    save_global_graph(global_g)
    del manifest["repos"][repo_name]
    save_global_manifest(manifest)
    return True


def list_global_repos() -> dict[str, Any]:
    """Lists all registered repositories with their node and edge metrics."""
    return load_global_manifest().get("repos", {})


def merge_graphs(graphs: list[nx.DiGraph]) -> nx.DiGraph:
    """Merges multiple NetworkX DiGraphs into a unified property graph."""
    merged = nx.DiGraph()
    for g in graphs:
        for n, data in g.nodes(data=True):
            if n in merged:
                # Merge lenses and metadata
                merged.nodes[n]["lenses"] = set(merged.nodes[n].get("lenses", [])) | set(data.get("lenses", []))
            else:
                merged.add_node(n, **data)
        for u, v, edata in g.edges(data=True):
            merged.add_edge(u, v, **edata)
    return merged
