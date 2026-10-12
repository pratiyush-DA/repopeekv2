"""Mermaid-based architecture and call-flow HTML report exporter."""
from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

import networkx as nx


def _sanitize_mermaid_id(name: str) -> str:
    """Sanitizes identifier for safe use in Mermaid diagrams."""
    clean = re.sub(r"[^A-Za-z0-9_]", "_", name)
    return clean.strip("_") or "node"


def generate_callflow_mermaid(graph: nx.DiGraph, max_edges: int = 50) -> str:
    """Generates a Mermaid.js flowchart string from graph calls and dependencies."""
    lines = ["graph LR"]

    # Filter to most significant edges (CALLS, INVOKES, READS, WRITES, IMPORTS)
    edges_to_render = []
    for u, v, data in graph.edges(data=True):
        rel = data.get("relation", "DEPENDS_ON").upper()
        edges_to_render.append((u, v, rel))

    for u, v, rel in edges_to_render[:max_edges]:
        u_id = _sanitize_mermaid_id(u)
        v_id = _sanitize_mermaid_id(v)
        u_lbl = html.escape(graph.nodes[u].get("label", u))
        v_lbl = html.escape(graph.nodes[v].get("label", v))
        lines.append(f'    {u_id}["{u_lbl}"] -->|{rel}| {v_id}["{v_lbl}"]')

    return "\n".join(lines)


def export_callflow_html(
    graph: nx.DiGraph,
    output_path: Path | str,
    title: str = "RepoPeek Architecture & Call Flow",
) -> Path:
    """Renders a standalone interactive HTML document featuring Mermaid architecture diagrams."""
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    mermaid_code = generate_callflow_mermaid(graph, max_edges=60)

    # Compile call table
    rows = []
    for u, v, data in list(graph.edges(data=True))[:100]:
        u_lbl = graph.nodes[u].get("label", u)
        v_lbl = graph.nodes[v].get("label", v)
        u_file = graph.nodes[u].get("file_path", "")
        v_file = graph.nodes[v].get("file_path", "")
        rel = data.get("relation", "DEPENDS_ON")
        conf = data.get("confidence", 1.0)
        rows.append(
            f"<tr><td><code>{html.escape(u_lbl)}</code><br><small>{html.escape(u_file)}</small></td>"
            f"<td><span class='badge'>{html.escape(rel)}</span></td>"
            f"<td><code>{html.escape(v_lbl)}</code><br><small>{html.escape(v_file)}</small></td>"
            f"<td>{conf*100:.0f}%</td></tr>"
        )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    :root {{
      --bg: #0f172a; --surface: #1e293b; --border: #334155;
      --text: #e2e8f0; --muted: #94a3b8; --accent: #38bdf8;
      --badge-bg: #0369a1;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      background: var(--bg); color: var(--text); line-height: 1.6;
      padding: 40px 24px;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    h1 {{
      font-size: 2.2rem; margin-bottom: 8px;
      background: linear-gradient(135deg, var(--accent), #a78bfa);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    p.subtitle {{ color: var(--muted); margin-bottom: 32px; font-size: 1.05rem; }}
    .card {{
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 12px; padding: 24px; margin-bottom: 32px;
    }}
    .mermaid {{ overflow-x: auto; padding: 16px 0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 0.95rem; }}
    th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); }}
    th {{ color: var(--accent); font-weight: 600; text-transform: uppercase; font-size: 0.8rem; }}
    code {{ color: #38bdf8; background: #0f172a; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
    small {{ color: var(--muted); }}
    .badge {{
      background: var(--badge-bg); color: #fff; padding: 3px 8px;
      border-radius: 6px; font-size: 0.75rem; font-weight: 600;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{html.escape(title)}</h1>
    <p class="subtitle">Architecture and Call Flow Visualization with Cross-Language Traceability</p>

    <div class="card">
      <h2 style="color: var(--accent); margin-bottom: 16px; font-size: 1.3rem;">Interactive Call Graph (Mermaid)</h2>
      <div class="mermaid">
{mermaid_code}
      </div>
    </div>

    <div class="card">
      <h2 style="color: var(--accent); margin-bottom: 16px; font-size: 1.3rem;">Call Flow Breakdown ({len(rows)} connections)</h2>
      <table>
        <thead>
          <tr>
            <th>Caller Symbol & File</th>
            <th>Relationship</th>
            <th>Callee Symbol & Target</th>
            <th>Confidence</th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows)}
        </tbody>
      </table>
    </div>
  </div>
  <script>
    mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
  </script>
</body>
</html>
"""
    out_file.write_text(html_content, encoding="utf-8")
    return out_file
