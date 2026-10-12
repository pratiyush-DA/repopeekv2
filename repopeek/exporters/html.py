"""Standalone High-Performance Obsidian-Style Interactive Canvas Graph Viewer.

Implements:
- HTML5 Canvas 2D engine with HiDPI / window.devicePixelRatio support for 60 FPS rendering.
- Screen-space font clamping and multi-tier Level-of-Detail (LOD) to prevent zoom breakage.
- Dynamic relevance-based node sizing via logarithmic degree centrality.
- Two-tier Blast Radius spotlighting (instant hover highlight + click-to-pin reachability).
- Obsidian dark theme parity (#161618), glassmorphic controls, and live force sliders.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import networkx as nx


def export_interactive_html(
    graph: nx.DiGraph,
    output_path: Path | str,
    telemetry_summary: dict[str, Any] | None = None,
) -> Path:
    """Exports the graph to a self-contained high-performance Canvas HTML visualization."""
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Format nodes and links for D3 force simulation with relevance metrics
    nodes_data = []
    node_id_map = {}
    
    for idx, (n_id, data) in enumerate(graph.nodes(data=True)):
        node_id_map[n_id] = idx
        in_deg = graph.in_degree(n_id)
        out_deg = graph.out_degree(n_id)
        total_deg = in_deg + out_deg
        external = bool(data.get("external", False))

        # Logarithmic relevance radius: min 3.5px, max 22.0px
        if external:
            radius = 3.5
        else:
            radius = round(min(22.0, max(3.5, 3.5 + 3.2 * math.log(1 + total_deg))), 2)

        nodes_data.append({
            "id": n_id,
            "label": data.get("label", n_id.split("::")[-1].split(":")[-1]),
            "kind": data.get("kind", "symbol"),
            "file": data.get("file_path", ""),
            "start_line": data.get("start_line", 1),
            "end_line": data.get("end_line", 1),
            "community": data.get("community_id", data.get("community", 0)),
            "lenses": sorted(list(data.get("lenses", []))),
            "reads": data.get("reads", []),
            "writes": data.get("writes", []),
            "raises": data.get("raises", []),
            "docstring": data.get("docstring", ""),
            "external": external,
            "in_degree": in_deg,
            "out_degree": out_deg,
            "degree": total_deg,
            "radius": radius,
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
<title>RepoPeek V2 - Obsidian Graph View</title>
<style>
  :root {{
    --bg-dark: #161618;
    --panel-bg: rgba(24, 25, 28, 0.90);
    --border-color: #2a2e37;
    --text-main: #dcddde;
    --text-muted: #8a8d93;
    --accent-red: #e05561;
    --accent-red-glow: rgba(224, 85, 97, 0.35);
    --accent-blue: #58a6ff;
    --node-default: #c9d1d9;
    --edge-default: rgba(70, 75, 86, 0.28);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg-dark);
    color: var(--text-main);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    overflow: hidden;
    height: 100vh;
    width: 100vw;
    user-select: none;
  }}

  #graph-canvas {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    cursor: grab;
  }}
  #graph-canvas:active {{
    cursor: grabbing;
  }}

  /* Top Navigation & Controls */
  #header-bar {{
    position: absolute;
    top: 14px;
    left: 18px;
    right: 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 100;
    pointer-events: none;
  }}
  .ui-panel {{
    pointer-events: auto;
    background: var(--panel-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 7px 14px;
    display: flex;
    gap: 10px;
    align-items: center;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45);
  }}
  .brand-group {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .nav-btn {{
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 15px;
    cursor: pointer;
    padding: 2px 4px;
    display: flex;
    align-items: center;
    transition: color 0.15s;
  }}
  .nav-btn:hover {{ color: var(--text-main); }}
  .title-text {{
    font-size: 13px;
    font-weight: 600;
    color: var(--text-main);
    letter-spacing: 0.2px;
  }}

  /* Search Input */
  .search-wrapper {{
    position: relative;
    display: flex;
    align-items: center;
  }}
  .search-input {{
    background: rgba(16, 17, 20, 0.8);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-main);
    font-size: 12px;
    padding: 5px 24px 5px 10px;
    outline: none;
    width: 170px;
    transition: width 0.2s, border-color 0.2s;
  }}
  .search-input:focus {{
    width: 230px;
    border-color: var(--accent-red);
  }}

  /* Right Tools & HUD */
  .hud-stat {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    font-size: 11px;
    padding: 0 4px;
  }}
  .hud-val {{
    font-weight: 700;
    color: #4cd964;
    font-size: 13px;
  }}
  .hud-label {{
    font-size: 9px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .icon-btn {{
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    border-radius: 6px;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.15s;
  }}
  .icon-btn:hover, .icon-btn.active {{
    background: rgba(224, 85, 97, 0.15);
    border-color: var(--accent-red);
    color: var(--accent-red);
  }}

  /* Floating Settings Drawer */
  #settings-panel {{
    position: absolute;
    top: 64px;
    right: 18px;
    width: 280px;
    background: var(--panel-bg);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 16px;
    z-index: 100;
    backdrop-filter: blur(14px);
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.6);
    display: none;
  }}
  #settings-panel.open {{ display: block; }}
  .settings-section {{ margin-bottom: 14px; }}
  .settings-title {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: var(--text-muted);
    margin-bottom: 10px;
  }}
  .control-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 9px;
    font-size: 12px;
  }}
  .control-row label {{ color: var(--text-main); }}
  .control-row input[type="range"] {{
    width: 120px;
    accent-color: var(--accent-red);
    cursor: pointer;
  }}
  .lens-chips {{
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }}
  .lens-chip {{
    background: rgba(40, 44, 52, 0.8);
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.15s;
  }}
  .lens-chip.active {{
    background: var(--accent-red);
    color: #ffffff;
    font-weight: 600;
    border-color: var(--accent-red);
  }}

  /* Hover Blast Radius Tooltip */
  #hover-tooltip {{
    position: absolute;
    pointer-events: none;
    z-index: 120;
    background: rgba(18, 19, 22, 0.94);
    border: 1px solid var(--accent-red);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
    display: none;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.7);
    max-width: 320px;
    transform: translate(12px, 12px);
  }}
  #hover-tooltip .tt-title {{
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 3px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  #hover-tooltip .tt-sub {{
    color: var(--text-muted);
    font-size: 11px;
  }}
  #hover-tooltip .tt-badge {{
    display: inline-block;
    background: rgba(224, 85, 97, 0.2);
    color: var(--accent-red);
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 10px;
    margin-top: 4px;
  }}

  /* Bottom Details Drawer */
  #details-drawer {{
    position: absolute;
    bottom: 20px;
    right: 20px;
    width: 380px;
    max-height: 440px;
    overflow-y: auto;
    background: var(--panel-bg);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 18px;
    z-index: 100;
    display: none;
    backdrop-filter: blur(14px);
    box-shadow: 0 10px 32px rgba(0, 0, 0, 0.65);
  }}
  #details-drawer h3 {{
    font-size: 15px;
    color: var(--accent-red);
    margin-bottom: 6px;
    word-break: break-all;
  }}
  #details-drawer p {{
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.5;
    margin-bottom: 8px;
  }}
  .badge {{
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 10px;
    background: #21262d;
    border: 1px solid var(--border-color);
    color: var(--text-main);
    margin-right: 4px;
    margin-bottom: 4px;
  }}
  .close-drawer-btn {{
    position: absolute;
    top: 14px;
    right: 14px;
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 16px;
    cursor: pointer;
  }}
  .close-drawer-btn:hover {{ color: var(--text-main); }}
</style>
<script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>

<canvas id="graph-canvas"></canvas>

<!-- Top Header Bar -->
<div id="header-bar">
  <div class="ui-panel brand-group">
    <button class="nav-btn" title="Back">&#8592;</button>
    <button class="nav-btn" title="Forward">&#8594;</button>
    <span class="title-text">Graph view</span>
    <div class="search-wrapper">
      <input type="text" id="node-search" class="search-input" placeholder="Search files & symbols..."/>
    </div>
  </div>

  <div class="ui-panel" style="gap:16px;">
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
    <button id="btn-recenter" class="icon-btn" title="Center & Recalibrate Graph">&#8982;</button>
    <button id="btn-settings" class="icon-btn" title="Graph View Settings">&#9881;</button>
  </div>
</div>

<!-- Settings Panel -->
<div id="settings-panel">
  <div class="settings-section">
    <div class="settings-title">Lenses & Filters</div>
    <div class="lens-chips">
      <button class="lens-chip active" onclick="setLens('ALL')">All</button>
      <button class="lens-chip" onclick="setLens('Call')">Call</button>
      <button class="lens-chip" onclick="setLens('Module')">Module</button>
      <button class="lens-chip" onclick="setLens('Class')">Class</button>
      <button class="lens-chip" onclick="setLens('Data')">Data</button>
      <button class="lens-chip" onclick="setLens('Entity')">Entity</button>
      <button class="lens-chip" onclick="setLens('Config')">Config</button>
      <button class="lens-chip" onclick="setLens('Process')">Process</button>
    </div>
  </div>

  <div class="settings-section">
    <div class="settings-title">Forces</div>
    <div class="control-row">
      <label>Repel force</label>
      <input type="range" id="slider-repel" min="40" max="400" value="140"/>
    </div>
    <div class="control-row">
      <label>Link distance</label>
      <input type="range" id="slider-distance" min="20" max="180" value="55"/>
    </div>
    <div class="control-row">
      <label>Center force</label>
      <input type="range" id="slider-center" min="1" max="10" value="4"/>
    </div>
  </div>

  <div class="settings-section">
    <div class="settings-title">Display</div>
    <div class="control-row">
      <label>Node size</label>
      <input type="range" id="slider-nodesize" min="5" max="25" value="10"/>
    </div>
    <div class="control-row">
      <label>Link thickness</label>
      <input type="range" id="slider-linkthickness" min="5" max="30" value="10"/>
    </div>
    <div class="control-row">
      <label>Show text</label>
      <input type="checkbox" id="toggle-text" checked style="accent-color:var(--accent-red);"/>
    </div>
  </div>
</div>

<!-- Hover Blast Radius HUD -->
<div id="hover-tooltip">
  <div class="tt-title" id="tt-title">Symbol Title</div>
  <div class="tt-sub" id="tt-file">File path</div>
  <div class="tt-badge" id="tt-blast">Blast Radius: 0 connected</div>
</div>

<!-- Details Drawer -->
<div id="details-drawer">
  <button class="close-drawer-btn" onclick="closeDrawer()">&times;</button>
  <h3 id="drawer-title">Symbol Title</h3>
  <p id="drawer-sub">File: line</p>
  <div id="drawer-badges"></div>
  <div id="drawer-blast-stats" style="margin-top:8px; font-size:12px; color:var(--text-main);"></div>
  <p id="drawer-desc" style="margin-top:10px;"></p>
</div>

<script>
const graphData = {graph_json};
const telemetryData = {telemetry_json};

const canvas = document.getElementById("graph-canvas");
const ctx = canvas.getContext("2d");

let width = window.innerWidth;
let height = window.innerHeight;
const dpr = window.devicePixelRatio || 1;

function resizeCanvas() {{
  width = window.innerWidth;
  height = window.innerHeight;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  canvas.style.width = width + "px";
  canvas.style.height = height + "px";
  requestRender();
}}
window.addEventListener("resize", resizeCanvas);

// Global State
let transform = d3.zoomIdentity;
let activeLens = "ALL";
let searchQuery = "";
let hoveredNode = null;
let pinnedNode = null;
let hoveredNeighbors = new Set();
let hoveredEdges = new Set();

let nodeSizeScale = 1.0;
let linkThicknessScale = 1.0;
let showTextLabels = true;

// Precompute adjacency map and edge map for instant O(1) blast radius lookup
const adjMap = new Map();
const edgeMap = new Map();
const nodeById = new Map();

graphData.nodes.forEach(n => {{
  adjMap.set(n.id, new Set());
  edgeMap.set(n.id, new Set());
  nodeById.set(n.id, n);
}});

graphData.links.forEach(l => {{
  const src = typeof l.source === "object" ? l.source.id : l.source;
  const tgt = typeof l.target === "object" ? l.target.id : l.target;
  if (adjMap.has(src)) adjMap.get(src).add(tgt);
  if (adjMap.has(tgt)) adjMap.get(tgt).add(src);
  if (edgeMap.has(src)) edgeMap.get(src).add(l);
  if (edgeMap.has(tgt)) edgeMap.get(tgt).add(l);
}});

// Simulation setup
const simulation = d3.forceSimulation(graphData.nodes)
  .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(55))
  .force("charge", d3.forceManyBody().strength(-140).theta(0.85))
  .force("center", d3.forceCenter(width / 2, height / 2).strength(0.04))
  .force("collide", d3.forceCollide().radius(d => d.radius + 4))
  .alphaDecay(0.028);

// Zoom setup
const zoom = d3.zoom()
  .scaleExtent([0.05, 12])
  .on("zoom", (e) => {{
    transform = e.transform;
    requestRender();
  }});

d3.select(canvas).call(zoom);

let animFrame = null;
function requestRender() {{
  if (!animFrame) {{
    animFrame = requestAnimationFrame(() => {{
      render();
      animFrame = null;
    }});
  }}
}}

simulation.on("tick", requestRender);

// Render pipeline
function render() {{
  ctx.save();
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.scale(dpr, dpr);
  ctx.translate(transform.x, transform.y);
  ctx.scale(transform.k, transform.k);

  const k = transform.k;
  const activeFocus = pinnedNode || hoveredNode;

  // 1. Draw Links
  for (let i = 0; i < graphData.links.length; i++) {{
    const l = graphData.links[i];
    const src = l.source;
    const tgt = l.target;

    // Filter by lens
    if (activeLens !== "ALL" && !l.lenses.includes(activeLens)) continue;

    const isConnected = activeFocus && (src.id === activeFocus.id || tgt.id === activeFocus.id);

    if (activeFocus) {{
      if (isConnected) {{
        ctx.strokeStyle = "#e05561";
        ctx.lineWidth = 1.8 / k;
        ctx.globalAlpha = 0.95;
      }} else {{
        ctx.strokeStyle = "#252830";
        ctx.lineWidth = 0.6 / k;
        ctx.globalAlpha = 0.02;
      }}
    }} else {{
      ctx.strokeStyle = "rgba(70, 75, 86, 0.28)";
      ctx.lineWidth = (0.8 * linkThicknessScale) / k;
      ctx.globalAlpha = 0.65;
    }}

    ctx.beginPath();
    ctx.moveTo(src.x, src.y);
    ctx.lineTo(tgt.x, tgt.y);
    ctx.stroke();
  }}

  // 2. Draw Nodes
  for (let i = 0; i < graphData.nodes.length; i++) {{
    const n = graphData.nodes[i];
    if (activeLens !== "ALL" && !n.lenses.includes(activeLens)) continue;

    const isTarget = activeFocus && n.id === activeFocus.id;
    const isNeighbor = activeFocus && hoveredNeighbors.has(n.id);
    const r = (n.radius * nodeSizeScale);

    if (activeFocus) {{
      if (isTarget) {{
        // Glowing halo for focused node
        ctx.globalAlpha = 0.35;
        ctx.fillStyle = "#e05561";
        ctx.beginPath();
        ctx.arc(n.x, n.y, r + 4 / k, 0, Math.PI * 2);
        ctx.fill();

        ctx.globalAlpha = 1.0;
        ctx.fillStyle = "#e05561";
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1.6 / k;
        ctx.stroke();
      }} else if (isNeighbor) {{
        ctx.globalAlpha = 1.0;
        ctx.fillStyle = "#f0f6fc";
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = "#e05561";
        ctx.lineWidth = 1.2 / k;
        ctx.stroke();
      }} else {{
        // Dim non-connected nodes
        ctx.globalAlpha = 0.06;
        ctx.fillStyle = n.external ? "#6e7681" : "#8b949e";
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fill();
      }}
    }} else {{
      // Resting neutral state
      const isSearchMatch = searchQuery && n.label.toLowerCase().includes(searchQuery);
      ctx.globalAlpha = isSearchMatch ? 1.0 : (searchQuery ? 0.15 : 0.95);
      ctx.fillStyle = isSearchMatch ? "#ff7b89" : (n.external ? "#6e7681" : "#c9d1d9");
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = "#161618";
      ctx.lineWidth = 1.0 / k;
      ctx.stroke();
    }}
  }}

  // 3. Screen-Space Crisp Text Labels (LOD Clamped)
  if (showTextLabels) {{
    const opticalSize = Math.max(9.5, Math.min(13, 11 / Math.pow(k, 0.15)));
    ctx.font = `${{opticalSize / k}}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";

    for (let i = 0; i < graphData.nodes.length; i++) {{
      const n = graphData.nodes[i];
      if (activeLens !== "ALL" && !n.lenses.includes(activeLens)) continue;

      const isTarget = activeFocus && n.id === activeFocus.id;
      const isNeighbor = activeFocus && hoveredNeighbors.has(n.id);
      const r = (n.radius * nodeSizeScale);

      let renderLabel = false;
      if (isTarget || isNeighbor) {{
        renderLabel = true;
      }} else if (!activeFocus) {{
        if (searchQuery && n.label.toLowerCase().includes(searchQuery)) {{
          renderLabel = true;
        }} else if (k < 0.6) {{
          renderLabel = n.degree >= 12;
        }} else if (k < 1.6) {{
          renderLabel = n.degree >= 4 || n.kind === "file" || n.kind === "module" || n.kind === "class";
        }} else {{
          renderLabel = true;
        }}
      }}

      if (renderLabel) {{
        ctx.globalAlpha = isTarget ? 1.0 : (isNeighbor ? 0.95 : 0.85);
        ctx.fillStyle = isTarget ? "#ffffff" : (isNeighbor ? "#e6edf3" : "#8b949e");
        ctx.fillText(n.label, n.x + r + 4 / k, n.y);
      }}
    }}
  }}

  ctx.restore();
}}

// Fast Spatial Hit Testing
function getNodeAt(screenX, screenY) {{
  const wx = (screenX - transform.x) / transform.k;
  const wy = (screenY - transform.y) / transform.k;
  const k = transform.k;

  for (let i = graphData.nodes.length - 1; i >= 0; i--) {{
    const n = graphData.nodes[i];
    if (activeLens !== "ALL" && !n.lenses.includes(activeLens)) continue;
    const r = (n.radius * nodeSizeScale) + (5 / k);
    const dx = wx - n.x;
    const dy = wy - n.y;
    if (dx * dx + dy * dy <= r * r) {{
      return n;
    }}
  }}
  return null;
}}

// Pointer Events: Hover Spotlight & Tooltip
const tooltip = document.getElementById("hover-tooltip");

canvas.addEventListener("mousemove", (e) => {{
  if (d3.event && d3.event.sourceEvent) return;
  const rect = canvas.getBoundingClientRect();
  const screenX = e.clientX - rect.left;
  const screenY = e.clientY - rect.top;
  const node = getNodeAt(screenX, screenY);

  if (node) {{
    if (!hoveredNode || hoveredNode.id !== node.id) {{
      hoveredNode = node;
      hoveredNeighbors = adjMap.get(node.id) || new Set();
      hoveredEdges = edgeMap.get(node.id) || new Set();
      requestRender();
    }}

    // Update tooltip
    tooltip.style.display = "block";
    tooltip.style.left = e.clientX + "px";
    tooltip.style.top = e.clientY + "px";
    document.getElementById("tt-title").innerText = node.label;
    document.getElementById("tt-file").innerText = `${{node.file || 'Symbol'}} (deg: ${{node.degree}})`;
    document.getElementById("tt-blast").innerText = `Blast Radius: ${{hoveredNeighbors.size}} direct connections`;
  }} else {{
    if (hoveredNode && !pinnedNode) {{
      hoveredNode = null;
      hoveredNeighbors.clear();
      hoveredEdges.clear();
      requestRender();
    }}
    tooltip.style.display = "none";
  }}
}});

canvas.addEventListener("mouseleave", () => {{
  tooltip.style.display = "none";
  if (!pinnedNode) {{
    hoveredNode = null;
    hoveredNeighbors.clear();
    hoveredEdges.clear();
    requestRender();
  }}
}});

// Click to Pin / Open Details Drawer
canvas.addEventListener("click", (e) => {{
  const rect = canvas.getBoundingClientRect();
  const screenX = e.clientX - rect.left;
  const screenY = e.clientY - rect.top;
  const node = getNodeAt(screenX, screenY);

  if (node) {{
    pinnedNode = node;
    hoveredNode = node;
    hoveredNeighbors = adjMap.get(node.id) || new Set();
    hoveredEdges = edgeMap.get(node.id) || new Set();
    showDetails(node);
    requestRender();
  }} else {{
    if (pinnedNode) {{
      pinnedNode = null;
      hoveredNode = null;
      hoveredNeighbors.clear();
      hoveredEdges.clear();
      closeDrawer();
      requestRender();
    }}
  }}
}});

// Node Dragging
d3.select(canvas).call(
  d3.drag()
    .subject((e) => {{
      const rect = canvas.getBoundingClientRect();
      return getNodeAt(e.x - rect.left, e.y - rect.top);
    }})
    .on("start", (e) => {{
      if (!e.subject) return;
      if (!e.active) simulation.alphaTarget(0.3).restart();
      e.subject.fx = e.subject.x;
      e.subject.fy = e.subject.y;
    }})
    .on("drag", (e) => {{
      if (!e.subject) return;
      e.subject.fx = (e.x - transform.x) / transform.k;
      e.subject.fy = (e.y - transform.y) / transform.k;
    }})
    .on("end", (e) => {{
      if (!e.subject) return;
      if (!e.active) simulation.alphaTarget(0);
      e.subject.fx = null;
      e.subject.fy = null;
    }})
);

// Search Handling
document.getElementById("node-search").addEventListener("input", (e) => {{
  searchQuery = e.target.value.trim().toLowerCase();
  requestRender();
}});

// Controls and Sliders
const settingsPanel = document.getElementById("settings-panel");
document.getElementById("btn-settings").addEventListener("click", () => {{
  settingsPanel.classList.toggle("open");
}});

document.getElementById("btn-recenter").addEventListener("click", () => {{
  d3.select(canvas).transition().duration(600).call(
    zoom.transform,
    d3.zoomIdentity.translate(width / 2, height / 2).scale(0.85).translate(-width / 2, -height / 2)
  );
}});

document.getElementById("slider-repel").addEventListener("input", (e) => {{
  simulation.force("charge").strength(-Number(e.target.value));
  simulation.alpha(0.3).restart();
}});

document.getElementById("slider-distance").addEventListener("input", (e) => {{
  simulation.force("link").distance(Number(e.target.value));
  simulation.alpha(0.3).restart();
}});

document.getElementById("slider-center").addEventListener("input", (e) => {{
  simulation.force("center").strength(Number(e.target.value) / 100);
  simulation.alpha(0.3).restart();
}});

document.getElementById("slider-nodesize").addEventListener("input", (e) => {{
  nodeSizeScale = Number(e.target.value) / 10;
  requestRender();
}});

document.getElementById("slider-linkthickness").addEventListener("input", (e) => {{
  linkThicknessScale = Number(e.target.value) / 10;
  requestRender();
}});

document.getElementById("toggle-text").addEventListener("change", (e) => {{
  showTextLabels = e.target.checked;
  requestRender();
}});

function setLens(lens) {{
  activeLens = lens;
  document.querySelectorAll(".lens-chip").forEach(b => {{
    b.classList.toggle("active", b.innerText === lens || (lens === "ALL" && b.innerText === "All"));
  }});
  requestRender();
}}

function showDetails(d) {{
  const drawer = document.getElementById("details-drawer");
  drawer.style.display = "block";
  document.getElementById("drawer-title").innerText = d.label;
  document.getElementById("drawer-sub").innerText = `${{d.file}} (L${{d.start_line}}-L${{d.end_line}})`;
  
  const badges = document.getElementById("drawer-badges");
  badges.innerHTML = `<span class="badge">Kind: ${{d.kind}}</span><span class="badge">Comm: ${{d.community}}</span>`;
  d.lenses.forEach(l => badges.innerHTML += `<span class="badge" style="background:#e05561; color:#fff;">${{l}}</span>`);

  const blastStats = document.getElementById("drawer-blast-stats");
  const conns = adjMap.get(d.id) || new Set();
  blastStats.innerHTML = `<strong>In-Degree:</strong> ${{d.in_degree}} | <strong>Out-Degree:</strong> ${{d.out_degree}} | <strong>Blast Radius:</strong> ${{conns.size}} symbols`;

  let text = d.docstring ? d.docstring : "No documentation comments.";
  if (d.reads && d.reads.length) text += `<br><strong>Reads:</strong> ${{d.reads.join(', ')}}`;
  if (d.writes && d.writes.length) text += `<br><strong>Writes:</strong> ${{d.writes.join(', ')}}`;
  if (d.raises && d.raises.length) text += `<br><strong>Raises:</strong> ${{d.raises.join(', ')}}`;
  document.getElementById("drawer-desc").innerHTML = text;
}}

function closeDrawer() {{
  document.getElementById("details-drawer").style.display = "none";
  pinnedNode = null;
  if (!hoveredNode) {{
    hoveredNeighbors.clear();
    hoveredEdges.clear();
  }}
  requestRender();
}}

// Initialize Canvas Size
resizeCanvas();
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
        assert "Obsidian Graph View" in content
        assert "graph-canvas" in content
        assert "fn_a" in content
        print("repopeek.exporters.html self-test passed!")
