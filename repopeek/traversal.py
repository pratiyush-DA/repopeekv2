"""Graph traversal, shortest path, node explanation, and semantic query engine."""
from __future__ import annotations

import re
from typing import Any

import networkx as nx


def resolve_node_id(graph: nx.DiGraph, query: str) -> str | None:
    """Resolves a node ID from an exact ID, file path, or symbol label."""
    if query in graph:
        return query

    query_lower = query.lower()

    # Exact label match
    for node_id, data in graph.nodes(data=True):
        if data.get("label", "").lower() == query_lower:
            return node_id

    # Suffix or partial match
    for node_id, data in graph.nodes(data=True):
        if query_lower in node_id.lower() or query_lower in data.get("label", "").lower():
            return node_id

    return None


def find_shortest_path(
    graph: nx.DiGraph,
    source: str,
    target: str,
    directed: bool = False,
) -> dict[str, Any]:
    """Finds the shortest path between source and target symbols with edge relation annotations."""
    src_id = resolve_node_id(graph, source)
    tgt_id = resolve_node_id(graph, target)

    if not src_id:
        return {"found": False, "error": f"Source symbol '{source}' not found in graph."}
    if not tgt_id:
        return {"found": False, "error": f"Target symbol '{target}' not found in graph."}

    search_graph = graph if directed else graph.to_undirected()

    try:
        path_nodes = nx.shortest_path(search_graph, source=src_id, target=tgt_id)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return {
            "found": False,
            "source": src_id,
            "target": tgt_id,
            "error": f"No path found between '{src_id}' and '{tgt_id}'.",
        }

    hops: list[dict[str, Any]] = []
    hop_texts: list[str] = []

    for i in range(len(path_nodes) - 1):
        u = path_nodes[i]
        v = path_nodes[i + 1]

        # Check edge direction in original graph
        relation = "CONNECTED_TO"
        confidence = 1.0
        direction = "->"

        if graph.has_edge(u, v):
            edata = graph[u][v]
            relation = edata.get("relation", "DEPENDS_ON")
            confidence = edata.get("confidence", 1.0)
            direction = "->"
        elif graph.has_edge(v, u):
            edata = graph[v][u]
            relation = edata.get("relation", "DEPENDS_ON")
            confidence = edata.get("confidence", 1.0)
            direction = "<-"

        hops.append({
            "step": i + 1,
            "from": u,
            "to": v,
            "relation": relation,
            "confidence": confidence,
            "direction": direction,
        })

        u_label = graph.nodes[u].get("label", u)
        v_label = graph.nodes[v].get("label", v)
        if direction == "->":
            hop_texts.append(f"`{u_label}` --[{relation}]--> `{v_label}`")
        else:
            hop_texts.append(f"`{u_label}` <--[{relation}]-- `{v_label}`")

    summary_text = (
        f"Shortest path ({len(hops)} hops):\n  "
        + "\n  ".join(hop_texts)
    )

    return {
        "found": True,
        "source": src_id,
        "target": tgt_id,
        "hops_count": len(hops),
        "path_nodes": path_nodes,
        "hops": hops,
        "formatted_text": summary_text,
    }


def explain_node(graph: nx.DiGraph, query: str) -> dict[str, Any]:
    """Generates an exhaustive technical explanation of a symbol node."""
    node_id = resolve_node_id(graph, query)
    if not node_id:
        return {"found": False, "error": f"Symbol '{query}' not found in graph."}

    data = graph.nodes[node_id]
    label = data.get("label", node_id)
    kind = data.get("kind", "symbol")
    file_path = data.get("file_path", "")
    start_line = data.get("start_line", 0)
    end_line = data.get("end_line", 0)
    community = data.get("community", 0)
    lenses = sorted(list(data.get("lenses", [])))
    reads = data.get("reads", [])
    writes = data.get("writes", [])
    raises = data.get("raises", [])

    in_edges = list(graph.in_edges(node_id, data=True))
    out_edges = list(graph.out_edges(node_id, data=True))
    total_degree = len(in_edges) + len(out_edges)

    lines = [
        f"Node: {label} ({node_id})",
        f"  Source:    {file_path} L{start_line}-L{end_line}",
        f"  Kind:      {kind}",
        f"  Community: {community}",
        f"  Degree:    {total_degree} (in: {len(in_edges)}, out: {len(out_edges)})",
        f"  Lenses:    {', '.join(lenses) if lenses else 'None'}",
    ]

    if reads:
        lines.append(f"  Reads:     {', '.join(reads)}")
    if writes:
        lines.append(f"  Writes:    {', '.join(writes)}")
    if raises:
        lines.append(f"  Raises:    {', '.join(raises)}")

    lines.append("")
    lines.append(f"Connections ({total_degree}):")

    for _, v, edata in out_edges:
        vlbl = graph.nodes[v].get("label", v)
        rel = edata.get("relation", "DEPENDS_ON")
        conf = edata.get("confidence", 1.0)
        lines.append(f"  --> {vlbl} [{rel}] [{conf:.2f}] ({v})")

    for u, _, edata in in_edges:
        ulbl = graph.nodes[u].get("label", u)
        rel = edata.get("relation", "DEPENDS_ON")
        conf = edata.get("confidence", 1.0)
        lines.append(f"  <-- {ulbl} [{rel}] [{conf:.2f}] ({u})")

    return {
        "found": True,
        "node_id": node_id,
        "label": label,
        "kind": kind,
        "file_path": file_path,
        "start_line": start_line,
        "end_line": end_line,
        "community": community,
        "degree": total_degree,
        "in_degree": len(in_edges),
        "out_degree": len(out_edges),
        "lenses": lenses,
        "reads": reads,
        "writes": writes,
        "raises": raises,
        "in_edges": [{"source": u, "relation": edata.get("relation", ""), "confidence": edata.get("confidence", 1.0)} for u, _, edata in in_edges],
        "out_edges": [{"target": v, "relation": edata.get("relation", ""), "confidence": edata.get("confidence", 1.0)} for _, v, edata in out_edges],
        "formatted_text": "\n".join(lines),
    }


def query_graph(
    graph: nx.DiGraph,
    question: str,
    mode: str = "bfs",
    max_nodes: int = 15,
    budget_tokens: int = 1500,
) -> dict[str, Any]:
    """Performs natural-language BFS or DFS graph traversal expanded across node vocabulary."""
    tokens = set(re.findall(r"[A-Za-z0-9_]{3,}", question.lower()))
    if not tokens:
        return {"nodes": [], "edges": [], "formatted_text": "No search tokens identified in question."}

    seed_scores: list[tuple[str, int]] = []
    for node_id, data in graph.nodes(data=True):
        score = 0
        lbl = data.get("label", "").lower()
        fp = data.get("file_path", "").lower()
        nid = node_id.lower()

        for t in tokens:
            if t == lbl:
                score += 5
            elif t in lbl:
                score += 3
            if t in nid:
                score += 2
            if t in fp:
                score += 1

        if score > 0:
            seed_scores.append((node_id, score))

    seed_scores.sort(key=lambda x: x[1], reverse=True)
    seeds = [nid for nid, _ in seed_scores[:5]]

    if not seeds:
        return {
            "nodes": [],
            "edges": [],
            "formatted_text": f"No matching concepts found for query '{question}'.",
        }

    visited: set[str] = set()
    collected_nodes: list[str] = []

    if mode.lower() == "dfs":
        for s in seeds:
            if len(collected_nodes) >= max_nodes:
                break
            for node in nx.dfs_preorder_nodes(graph, source=s):
                if node not in visited:
                    visited.add(node)
                    collected_nodes.append(node)
                    if len(collected_nodes) >= max_nodes:
                        break
    else:
        # Default BFS
        queue = list(seeds)
        for s in seeds:
            visited.add(s)

        while queue and len(collected_nodes) < max_nodes:
            curr = queue.pop(0)
            collected_nodes.append(curr)

            neighbors = list(graph.successors(curr)) + list(graph.predecessors(curr))
            for nbr in neighbors:
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
                    if len(collected_nodes) + len(queue) >= max_nodes * 2:
                        break

    subgraph = graph.subgraph(collected_nodes)

    lines = [
        f"## Query Result: '{question}'",
        f"Matched {len(collected_nodes)} nodes ({mode.upper()} traversal):\n",
    ]

    for n in collected_nodes:
        d = graph.nodes[n]
        lbl = d.get("label", n)
        fp = d.get("file_path", "")
        lines.append(f"- `{lbl}` ({d.get('kind', 'symbol')}) at `{fp}:L{d.get('start_line', 0)}`")

    lines.append("\nKey Traversal Edges:")
    for u, v, edata in subgraph.edges(data=True):
        u_lbl = graph.nodes[u].get("label", u)
        v_lbl = graph.nodes[v].get("label", v)
        lines.append(f"  `{u_lbl}` --[{edata.get('relation', 'DEPENDS_ON')}]--> `{v_lbl}`")

    return {
        "nodes": collected_nodes,
        "edges_count": subgraph.number_of_edges(),
        "seeds": seeds,
        "formatted_text": "\n".join(lines),
    }
