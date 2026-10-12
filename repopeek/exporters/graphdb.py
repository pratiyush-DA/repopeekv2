"""Graph database, GraphML, SVG, and Obsidian Canvas exporters."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import networkx as nx


def _clean_cypher_prop(val: Any) -> str:
    """Escapes string values for safe use in Cypher literals."""
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{s}'"


def export_cypher(graph: nx.DiGraph, output_path: Path | str) -> Path:
    """Generates Neo4j and FalkorDB compatible Cypher DDL and upsert statements."""
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "// RepoPeek V2 Cypher Export for Neo4j / FalkorDB",
        "// Indexes:",
        "CREATE INDEX node_id_idx IF NOT EXISTS FOR (n:Symbol) ON (n.id);",
        "",
        "// Nodes:",
    ]

    for n, data in graph.nodes(data=True):
        label = data.get("label", n)
        kind = data.get("kind", "symbol").capitalize()
        safe_kind = re.sub(r"[^A-Za-z0-9_]", "", kind) or "Symbol"
        fp = data.get("file_path", "")
        lines.append(
            f"MERGE (n:{safe_kind} {{id: {_clean_cypher_prop(n)}}}) "
            f"ON CREATE SET n.label = {_clean_cypher_prop(label)}, "
            f"n.file_path = {_clean_cypher_prop(fp)}, "
            f"n.community = {data.get('community', 0)};"
        )

    lines.append("\n// Edges:")
    for u, v, data in graph.edges(data=True):
        rel = data.get("relation", "DEPENDS_ON").upper()
        safe_rel = re.sub(r"[^A-Z0-9_]", "_", rel) or "DEPENDS_ON"
        conf = float(data.get("confidence", 1.0))
        lines.append(
            f"MATCH (a {{id: {_clean_cypher_prop(u)}}}), (b {{id: {_clean_cypher_prop(v)}}}) "
            f"MERGE (a)-[r:{safe_rel} {{confidence: {conf}}}]->(b);"
        )

    out_file.write_text("\n".join(lines), encoding="utf-8")
    return out_file


def export_graphml(graph: nx.DiGraph, output_path: Path | str) -> Path:
    """Exports graph in standard GraphML XML format for Gephi, Cytoscape, and yEd."""
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Format node attributes cleanly for GraphML serialization
    G_clean = nx.DiGraph()
    for n, data in graph.nodes(data=True):
        clean_d = {
            "label": str(data.get("label", n)),
            "kind": str(data.get("kind", "symbol")),
            "file_path": str(data.get("file_path", "")),
            "start_line": int(data.get("start_line", 0)),
            "community": int(data.get("community", 0)),
        }
        G_clean.add_node(n, **clean_d)

    for u, v, data in graph.edges(data=True):
        clean_e = {
            "relation": str(data.get("relation", "DEPENDS_ON")),
            "confidence": float(data.get("confidence", 1.0)),
        }
        G_clean.add_edge(u, v, **clean_e)

    nx.write_graphml(G_clean, str(out_file))
    return out_file


def export_canvas(graph: nx.DiGraph, output_path: Path | str, max_nodes: int = 50) -> Path:
    """Exports an Obsidian .canvas layout JSON file with visual nodes and connecting edge arrows."""
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    sub_nodes = list(graph.nodes())[:max_nodes]
    subgraph = graph.subgraph(sub_nodes)

    # Layout nodes in an organized grid
    canvas_nodes = []
    cols = 5
    card_w, card_h = 240, 120
    gap_x, gap_y = 60, 60

    for idx, n in enumerate(sub_nodes):
        d = graph.nodes[n]
        row = idx // cols
        col = idx % cols
        x = col * (card_w + gap_x)
        y = row * (card_h + gap_y)

        lbl = d.get("label", n)
        kind = d.get("kind", "symbol")
        fp = d.get("file_path", "")
        text = f"**{lbl}**\n`{kind}`\n`{fp}`"

        canvas_nodes.append({
            "id": n,
            "x": x,
            "y": y,
            "width": card_w,
            "height": card_h,
            "type": "text",
            "text": text,
        })

    canvas_edges = []
    for edge_idx, (u, v, data) in enumerate(subgraph.edges(data=True)):
        rel = data.get("relation", "DEPENDS_ON")
        canvas_edges.append({
            "id": f"edge_{edge_idx}",
            "fromNode": u,
            "fromSide": "right",
            "toNode": v,
            "toSide": "left",
            "label": rel,
        })

    canvas_data = {
        "nodes": canvas_nodes,
        "edges": canvas_edges,
    }

    out_file.write_text(json.dumps(canvas_data, indent=2), encoding="utf-8")
    return out_file


def export_svg(graph: nx.DiGraph, output_path: Path | str, max_nodes: int = 30) -> Path:
    """Generates a standalone vector SVG diagram for documentation embedding."""
    import math

    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    sub_nodes = list(graph.nodes())[:max_nodes]
    subgraph = graph.subgraph(sub_nodes)

    width, height = 1000, 700
    pos: dict[str, tuple[float, float]] = {}
    radius = min(width, height) * 0.38
    cx, cy = width / 2, height / 2
    n_count = len(sub_nodes)

    for i, n in enumerate(sub_nodes):
        angle = (2 * math.pi * i) / max(n_count, 1)
        pos[n] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">',
        f'<rect width="{width}" height="{height}" fill="#0f172a" />',
        '<defs>',
        '  <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '    <path d="M 0 0 L 10 5 L 0 10 z" fill="#38bdf8" />',
        '  </marker>',
        '</defs>',
    ]

    # Draw edges
    for u, v in subgraph.edges():
        if u in pos and v in pos:
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            svg_parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="#334155" stroke-width="1.5" marker-end="url(#arrow)" />'
            )

    # Draw nodes
    for n in sub_nodes:
        if n in pos:
            x, y = pos[n]
            lbl = graph.nodes[n].get("label", n)
            svg_parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12" fill="#0284c7" stroke="#38bdf8" stroke-width="2" />'
            )
            svg_parts.append(
                f'<text x="{x:.1f}" y="{y + 24:.1f}" fill="#e2e8f0" font-family="system-ui, sans-serif" '
                f'font-size="11" text-anchor="middle">{lbl}</text>'
            )

    svg_parts.append('</svg>')
    out_file.write_text("\n".join(svg_parts), encoding="utf-8")
    return out_file
