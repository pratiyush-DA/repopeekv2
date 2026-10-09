# 08 - Graphify Hybrid Integration Blueprint

## 1. Design Philosophy: The Hybrid Synthesis

The core mandate for this project is:
> **Do not reinvent a bespoke engine from scratch. Leverage Graphify's concrete codebase and solution architecture as the foundational substrate, and extend it to fulfill the full feature set and 11-tool MCP server interface required by RepoPeek.**

By treating `Reference/graphify` as the core operational platform rather than starting from zero, we eliminate hundreds of hours of duplicate effort, maximize architectural stability, and immediately benefit from Graphify's battle-tested 40+ language Tree-sitter parsers, Leiden clustering, NetworkX graphs, and multi-assistant support.

```
+----------------------------------------------------------------------------------------------------+
| HYBRID ARCHITECTURE: GRAPHIFY CORE + REPOPEEK CAPABILITY LAYER                                     |
|                                                                                                    |
| +------------------------------------------------------------------------------------------------+ |
| | REPOPEEK AGENT INTELLIGENCE INTERFACE (11 MCP Tools + Context Compiler + 9 Lenses + HUD)       | |
| | - repopeek_context (<=4 files, ~40-line snippets, token budget governor)                       | |
| | - repopeek_plan (step-by-step risk-assessed implementation plan)                                | |
| | - repopeek_impact (blast radius tree: callers, tables, routes)                                 | |
| | - repopeek_data_trace (state def-use flow: READS vs WRITES)                                     | |
| | - repopeek_routes (cross-language HTTP boundary bridge)                                        | |
| | - repopeek_co_changes (git commit temporal coupling matrix)                                    | |
| | - repopeek_savings (counterfactual token/cost ROI scoreboard)                                  | |
| | - repopeek_lookup, repopeek_neighbors, repopeek_context_pack, repopeek_resolve                 | |
| +------------------------------------------------------------------------------------------------+ |
|                                                ▲                                                   |
|                                                │  [Extends & Enriches]                             |
| +------------------------------------------------------------------------------------------------+ |
| | GRAPHIFY REUSABLE CORE SUBSTRATE (Reference/graphify)                                          | |
| | - Parser Substrate:    graphify/extract.py & extractors/ (40+ languages, 103+ extensions)      | |
| | - Graph Model:         graphify/build.py (NetworkX DiGraph, node-link JSON, dedup, arc order)  | |
| | - Clustering:          graphify/cluster.py (Leiden graspologic_native / Louvain partition)     | |
| | - Reachability:        graphify/affected.py & serve.py (BFS/DFS traversal, shortest path)      | |
| | - Slicing & Tokens:    graphify/file_slice.py (Span offsets, token budgeting)                  | |
| | - Server Engine:       graphify/serve.py (JSON-RPC stdio MCP 1.x & 2.x, Streamable HTTP ASGI)   | |
| | - Visualizers:         graphify/exporters/html.py (D3 force viewer) & export.py (Obsidian)     | |
| | - Incremental Watch:   graphify/watch.py (Debounced rebuild daemon)                            | |
| +------------------------------------------------------------------------------------------------+ |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Component Mapping & Extension Blueprint

| RepoPeek Target Capability | Graphify Baseline Substrate (`Reference/graphify`) | Exact Extension Required |
|---|---|---|
| **Polyglot Parsing (40+ Languages)** | `graphify/extract.py` (`_DISPATCH`, `_SHEBANG_DISPATCH`) & `graphify/extractors/*` | Retain all 40+ language extractors (103+ file extensions); enrich emitted node/edge payloads with start/end byte offsets, line spans, def-use facts, and HTTP client call metadata. |
| **Universal Namespace Isolation** | `graphify/ids.py`, `graphify/build.py` | Add prefix enforcement across all 40+ languages (`py:`, `ts:`, `go:`, `rs:`, `java:`, `c:`, `cpp:`, `cs:`, `rb:`, `php:`, `kt:`, `swift:`, `lua:`, `zig:`, `sh:`, `ps:`, `ex:`, `erl:`, `dart:`, `r:`, `jl:`, `ml:`, `lisp:`, `f:`, `pas:`, `cbl:`, `apex:`, `sol:`, `v:`, `dm:`, `tf:`, `robot:`, `sql:`, `cfg:`, `doc:`, `npm:`, `pip:`, etc.) to prevent string collisions across disconnected runtimes. |
| **9 Materialized Lenses** | `graphify/build.py`, `graphify/analyze.py` | Tag nodes and edges with matching lens memberships (`Module`, `Symbol`, `Call`, `Class`, `Data`, `Entity`, `Config`, `Process`, `Exception`). Add on-demand subgraph filter. |
| **HTTP Boundary Bridge** | `graphify/extractors/resolution.py` | Add path parameter normalizer (`:param`) matching client `fetch`/`axios` endpoints to backend route handlers, emitting `INVOKES` edges. |
| **SQL Data Def-Use** | `graphify/extractors/sql.py` | Augment SQL extraction to separate `READS` (`SELECT`) from `WRITES` (`INSERT`/`UPDATE`/`DELETE`) to database table nodes. |
| **Git Temporal Intelligence** | New module: `graphify/temporal.py` (sibling to `analyze.py`) | Mine git commit logs using 180-day exponential half-life decay; synthesize `CO_CHANGED_WITH` edges in NetworkX. |
| **Context Compiler (≤4 files)** | `graphify/file_slice.py` + `affected.py` | Combine blast-radius seed nodes with file spans to extract focused ~40-line snippets from at most 4 files (~1–2k tokens). |
| **11 Dual-Transport MCP Tools** | `graphify/serve.py` (`_handlers`, `list_tools`) | Register the 11 `repopeek_*` tools in `serve.py` using Graphify's existing `Server` and JSON-RPC dispatch loop across both stdio and HTTP transports. |
| **Telemetry & Savings HUD** | New module: `graphify/telemetry.py` | Track unconstrained blast-radius counterfactual baseline; calculate tokens saved, files avoided, and cost savings ($3/M tokens baseline). |
| **Interactive D3 Viewer** | `graphify/exporters/html.py` | Embed 9-lens filter tabs, one-click blast radius glowing path highlighting, and Telemetry HUD into Graphify's existing D3 force simulation. |
| **Obsidian Vault Export** | `graphify/export.py` (`to_obsidian`) | Retain Graphify's frontmatter and `[[wikilinks]]` generation; add `.obsidian/graph.json` color groupings for the 9 lenses. |
| **Incremental Watch Daemon** | `graphify/watch.py` | Adapt `_rebuild_code` to patch the in-memory NetworkX graph in <50ms instead of performing a full reload. |

---

## 3. Detailed MCP Server Adapter Specification

Graphify's `serve.py` already implements dual compatibility with `mcp 1.x` and `mcp 2.x`, project context caching (`_GraphContextCache`), and JSON-RPC stdio streaming. We extend `serve.py` by mapping RepoPeek's 11 tool handlers onto Graphify's internal functions:

```python
# Extending graphify/serve.py to expose RepoPeek's 11 tools

_handlers = {
    # 1. Exact node inspection
    "repopeek_lookup": lambda args: _tool_get_node(args),
    
    # 2. 1-hop inbound and outbound edges
    "repopeek_neighbors": lambda args: _tool_get_neighbors(args),
    
    # 3. Transitive blast radius
    "repopeek_impact": lambda args: _tool_repopeek_impact(G, args),
    
    # 4. State def-use tracing (READS/WRITES)
    "repopeek_data_trace": lambda args: _tool_repopeek_data_trace(G, args),
    
    # 5. Token-governed context pack for symbols
    "repopeek_context_pack": lambda args: _tool_repopeek_context_pack(G, args),
    
    # 6. Natural-language task context compiler (<=4 files, ~40-line spans)
    "repopeek_context": lambda args: _tool_repopeek_context(G, args),
    
    # 7. Step-by-step risk-assessed change planner
    "repopeek_plan": lambda args: _tool_repopeek_plan(G, args),
    
    # 8. Cross-language HTTP boundary routes
    "repopeek_routes": lambda args: _tool_repopeek_routes(G),
    
    # 9. Temporally coupled files from git history
    "repopeek_co_changes": lambda args: _tool_repopeek_co_changes(G, args),
    
    # 10. Natural-language symbol candidate ranking
    "repopeek_resolve": lambda args: _tool_repopeek_resolve(G, args),

    # 11. Quantifiable token and cost savings ROI scoreboard
    "repopeek_savings": lambda args: _tool_repopeek_savings(args),
}
```

---

## 4. Implementation Strategy: Clean Additive Architecture

Instead of modifying Graphify's core files in high-risk ways, all RepoPeek enhancements are designed as **additive, modular overlays**:

1. **`repopeek/` Package Root:**
   Houses the enhanced package, importing proven utilities from Graphify:
   - `from graphify.extract import extract, collect_files, _DISPATCH, _SHEBANG_DISPATCH`
   - `from graphify.cluster import cluster`
   - `from graphify.export import to_obsidian, to_json`
   - `from graphify.file_slice import unit_source_text`
   - `from graphify.serve import Server, _GraphContextCache`

2. **Polyglot Parser Wrapper (`repopeek.parsers.polyglot`):**
   Calls Graphify's `_safe_extract` across all 103+ extensions, applying RepoPeek's canonical namespace prefixing and line/byte-span enrichment.

3. **Context Engine (`repopeek.context`):**
   Wraps Graphify's `affected.py` and `file_slice.py` to enforce the strict **≤4 files cap**, **~40-line snippets**, and **1–2k token budget**.

4. **Telemetry Engine (`repopeek.telemetry`):**
   Intercepts tool calls to compute blast-radius counterfactual baseline savings, displaying in-line scorecards and populating `repopeek_savings`.
