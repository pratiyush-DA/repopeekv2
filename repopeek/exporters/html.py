"""Standalone D3 Obsidian-Style Interactive Graph Viewer with 9 Switchable Lenses and Savings HUD."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx


def export_interactive_html(
    graph: nx.DiGraph,
    output_path: Path | str,
    telemetry_summary: dict[str, Any] | None = None,
) -> Path:
    """Exports the graph to a self-contained interactive D3 HTML visualization."""
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Format nodes and links for D3 force simulation
    nodes_data = []
    node_id_map = {}
    for idx, (n_id, data) in enumerate(graph.nodes(data=True)):
        node_id_map[n_id] = idx
        nodes_data.append({
            "id": n_id,
            "label": data.get("label", n_id.split("::")[-1]),
            "kind": data.get("kind", "symbol"),
            "file": data.get("file_path", ""),
            "start_line": data.get("start_line", 1),
            "end_line": data.get("end_line", 1),
            "community": data.get("community", 0),
            "lenses": sorted(list(data.get("lenses", []))),
            "reads": data.get("reads", []),
            "writes": data.get("writes", []),
            "docstring": data.get("docstring", ""),
            "external": bool(data.get("external", False)),
        })

    links_data = []
    for u, v, data in graph.edges(data=True):
        if u in node_id_map and v in node_id_map:
            links_data.append({
                "source": u,
                "target": v,
                "relation": data.get("relation", "DEPENDS_ON"),
                "confidence": float(data.get("confidence", 1.0)),
                "lenses": sorted(list(data.get("lenses", []))),
                "evidence": data.get("evidence", ""),
            })

    telemetry = telemetry_summary or {
        "tasks_count": 0,
        "total_tokens_saved": 0,
        "total_files_avoided": 0,
        "total_cost_saved_usd": 0.0,
        "overall_reduction_pct": 0.0,
    }

    graph_json = json.dumps({"nodes": nodes_data, "links": links_data}, indent=2)
    telemetry_json = json.dumps(telemetry, indent=2)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>RepoPeek V2 - Semantic Code Property Graph</title>
<style>
  :root {{
    --bg-dark: #0f1117;
    --panel-bg: rgba(22, 27, 34, 0.92);
    --border-color: #30363d;
    --text-main: #e6edf3;
    --text-muted: #8b949e;
    --accent: #58a6ff;
    --accent-glow: #238636;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg-dark);
    color: var(--text-main);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    overflow: hidden;
    height: 100vh;
    width: 100vw;
  }}
  #navbar {{
    position: absolute;
    top: 12px;
    left: 16px;
    right: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 100;
    pointer-events: none;
  }}
  .nav-group {{
    pointer-events: auto;
    background: var(--panel-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 8px 14px;
    display: flex;
    gap: 8px;
    align-items: center;
    backdrop-filter: blur(10px);
  }}
  .lens-btn {{
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
  }}
  .lens-btn:hover, .lens-btn.active {{
    background: var(--accent);
    color: #0f1117;
    font-weight: 600;
    border-color: var(--accent);
  }}
  #hud {{
    font-size: 12px;
    display: flex;
    gap: 16px;
  }}
  .hud-stat {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
  }}
  .hud-val {{
    font-weight: 700;
    color: #3fb950;
    font-size: 14px;
  }}
  .hud-label {{
    font-size: 10px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  #canvas-container {{
    width: 100%;
    height: 100%;
  }}
  svg {{
    width: 100%;
    height: 100%;
  }}
  #details-drawer {{
    position: absolute;
    bottom: 20px;
    right: 20px;
    width: 380px;
    max-height: 400px;
    overflow-y: auto;
    background: var(--panel-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    z-index: 100;
    display: none;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
  }}
  #details-drawer h3 {{
    font-size: 15px;
    color: var(--accent);
    margin-bottom: 8px;
    word-break: break-all;
  }}
  #details-drawer p {{
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.5;
    margin-bottom: 6px;
  }}
  .badge {{
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    background: #21262d;
    border: 1px solid var(--border-color);
    color: var(--text-main);
    margin-right: 4px;
    margin-bottom: 4px;
  }}
</style>
<script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>

<div id="navbar">
  <div class="nav-group">
    <strong style="font-size:13px; color:#fff; margin-right:6px;">RepoPeek V2</strong>
    <button class="lens-btn active" onclick="setLens('ALL')">All</button>
    <button class="lens-btn" onclick="setLens('Call')">Call</button>
    <button class="lens-btn" onclick="setLens('Module')">Module</button>
    <button class="lens-btn" onclick="setLens('Class')">Class</button>
    <button class="lens-btn" onclick="setLens('Data')">Data</button>
    <button class="lens-btn" onclick="setLens('Entity')">Entity</button>
    <button class="lens-btn" onclick="setLens('Config')">Config</button>
    <button class="lens-btn" onclick="setLens('Process')">Process</button>
    <button class="lens-btn" onclick="setLens('Exception')">Exception</button>
  </div>

  <div class="nav-group" id="hud">
    <div class="hud-stat">
      <span class="hud-val" id="hud-tokens">{telemetry['total_tokens_saved']:,}</span>
      <span class="hud-label">Tokens Saved</span>
    </div>
    <div class="hud-stat">
      <span class="hud-val" id="hud-files">{telemetry['total_files_avoided']:,}</span>
      <span class="hud-label">Files Avoided</span>
    </div>
    <div class="hud-stat">
      <span class="hud-val" id="hud-cost">${telemetry['total_cost_saved_usd']:.2f}</span>
      <span class="hud-label">Est. Saved</span>
    </div>
  </div>
</div>

<div id="canvas-container">
  <svg id="graph-svg"></svg>
</div>

<div id="details-drawer">
  <h3 id="drawer-title">Symbol Title</h3>
  <p id="drawer-sub">File: line</p>
  <div id="drawer-badges"></div>
  <p id="drawer-desc" style="margin-top:10px;"></p>
</div>

<script>
const graphData = {graph_json};
const telemetryData = {telemetry_json};

const width = window.innerWidth;
const height = window.innerHeight;

const svg = d3.select("#graph-svg")
  .attr("viewBox", [0, 0, width, height]);

const g = svg.append("g");

svg.call(d3.zoom()
  .scaleExtent([0.1, 8])
  .on("zoom", (e) => g.attr("transform", e.transform))
);

let activeLens = "ALL";

const simulation = d3.forceSimulation(graphData.nodes)
  .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(60))
  .force("charge", d3.forceManyBody().strength(-180))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(25));

const link = g.append("g")
  .attr("stroke", "#30363d")
  .attr("stroke-opacity", 0.6)
  .selectAll("line")
  .data(graphData.links)
  .join("line")
  .attr("stroke-width", d => Math.max(1, d.confidence * 2));

const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

const node = g.append("g")
  .selectAll("circle")
  .data(graphData.nodes)
  .join("circle")
  .attr("r", d => d.external ? 4 : 7)
  .attr("fill", d => d.external ? "#8b949e" : colorScale(d.community))
  .attr("stroke", "#0f1117")
  .attr("stroke-width", 1.5)
  .style("cursor", "pointer")
  .call(drag(simulation))
  .on("click", (event, d) => showDetails(d));

const labels = g.append("g")
  .selectAll("text")
  .data(graphData.nodes)
  .join("text")
  .text(d => d.label)
  .attr("font-size", 9)
  .attr("fill", "#8b949e")
  .attr("dx", 10)
  .attr("dy", 3)
  .style("pointer-events", "none");

simulation.on("tick", () => {{
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);

  node
    .attr("cx", d => d.x)
    .attr("cy", d => d.y);

  labels
    .attr("x", d => d.x)
    .attr("y", d => d.y);
}});

function drag(sim) {{
  function dragstarted(event) {{
    if (!event.active) sim.alphaTarget(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
  }}
  function dragged(event) {{
    event.subject.fx = event.x;
    event.subject.fy = event.y;
  }}
  function dragended(event) {{
    if (!event.active) sim.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
  }}
  return d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended);
}}

function setLens(lens) {{
  activeLens = lens;
  document.querySelectorAll(".lens-btn").forEach(b => {{
    b.classList.toggle("active", b.innerText === lens || (lens === "ALL" && b.innerText === "All"));
  }});

  node.transition().duration(300)
    .style("opacity", d => (lens === "ALL" || d.lenses.includes(lens)) ? 1 : 0.1);

  link.transition().duration(300)
    .style("opacity", d => (lens === "ALL" || d.lenses.includes(lens)) ? 0.6 : 0.05);

  labels.transition().duration(300)
    .style("opacity", d => (lens === "ALL" || d.lenses.includes(lens)) ? 0.9 : 0.1);
}}

function showDetails(d) {{
  const drawer = document.getElementById("details-drawer");
  drawer.style.display = "block";
  document.getElementById("drawer-title").innerText = d.label;
  document.getElementById("drawer-sub").innerText = `${{d.file}} (L${{d.start_line}}-L${{d.end_line}})`;
  
  const badges = document.getElementById("drawer-badges");
  badges.innerHTML = `<span class="badge">Kind: ${{d.kind}}</span><span class="badge">Comm: ${{d.community}}</span>`;
  d.lenses.forEach(l => badges.innerHTML += `<span class="badge" style="background:#1f6feb;">${{l}}</span>`);

  let text = d.docstring ? d.docstring : "No documentation comments.";
  if (d.reads && d.reads.length) text += `<br><strong>Reads:</strong> ${{d.reads.join(', ')}}`;
  if (d.writes && d.writes.length) text += `<br><strong>Writes:</strong> ${{d.writes.join(', ')}}`;
  document.getElementById("drawer-desc").innerHTML = text;
}}
</script>
</body>
</html>
"""

    out_file.write_text(html_content, encoding="utf-8")
    return out_file


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        G = nx.DiGraph()
        G.add_node("py:a.py::fn_a", label="fn_a", kind="function", file_path="a.py", lenses={"Symbol", "Call"})
        G.add_node("py:b.py::fn_b", label="fn_b", kind="function", file_path="b.py", lenses={"Symbol", "Call"})
        G.add_edge("py:a.py::fn_a", "py:b.py::fn_b", relation="CALLS", lenses={"Call"})

        out = export_interactive_html(G, Path(tmp_dir) / "graph.html")
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "RepoPeek V2" in content
        assert "fn_a" in content
        print("repopeek.exporters.html self-test passed!")
