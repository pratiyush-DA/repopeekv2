# 01 - Executive Summary & Vision

## 1. Executive Summary

Autonomous AI coding agents (such as Hermes, Claude Code, Cursor, and Antigravity) encounter two fundamental bottlenecks when operating on complex, multi-language codebases:
1. **Context Bloat & Token Exhaustion:** Reading raw files or unstructured vector dumps pollutes the agent's context window, degrading reasoning precision and incurring high latency and API cost.
2. **Structural Blindness & Hallucination:** Agents lack a unified, cross-language mental model of symbol references, data-flow boundaries (SQL table writes, API client-to-route calls), configuration bindings, and temporal co-change relationships.

**RepoPeek** is an autonomous, local-first Semantic Code Property Graph (SCPG) intelligence engine. Rather than functioning as a closed-world code dump or a naive vector store, RepoPeek acts as the **primary navigation substrate** for coding agents. It indexes polyglot codebases into a property graph and deterministically compiles **task-specific context packs capped at ≤4 files with ~40-line spans** (~1–2k tokens).

RepoPeek adopts the proven structural AST parsing and community-clustering baseline from **Graphify**, advancing it into a production-grade multi-agent intelligence platform.

---

## 2. Problem Statement: Why Existing Approaches Fail

| Paradigm | Failure Mode | Impact on Coding Agents |
|---|---|---|
| **Vector RAG (Embeddings + Cosine)** | Semantic similarity misses exact lexical dependencies, data definitions, and call chains. Chunks lack caller/callee context. | Agent hallucinates method signatures, edits wrong overloads, or fails to notice breaking changes in callers. |
| **Monolithic AST / LSP Dumps** | LSP protocols operate per-language in isolated silos; full repo dumps exceed context windows. | Agent is overwhelmed by 50k+ tokens of irrelevant syntax; no cross-language linking (e.g. Python backend to TS frontend). |
| **Generic Knowledge Graphs** | Flat unconstrained graph traversal results in exponential graph explosions (e.g. traversing common names like `next` or `config`). | Blast-radius searches return hundreds of thousands of noisy nodes; context budgets blow out. |

---

## 3. The Baseline: Graphify Architectural Strengths & Gaps

Graphify provides a clean, local-first foundation:
- **Strengths Adopted:**
  - Fast, local-first AST parsing using Tree-sitter without requiring external servers or remote APIs.
  - Strict node and edge schema with confidence labeling (`EXTRACTED`, `INFERRED`, `AMBIGUOUS`).
  - NetworkX in-memory graph model with serialization to node-link JSON (`graph.json`).
  - Community clustering via Leiden/Louvain algorithms.
  - Standalone, zero-dependency interactive HTML graph visualization using D3 force simulation.
  - Native Obsidian vault export with bidirectional `[[wikilinks]]`.
  - Stdio MCP server integration for agent querying.
- **Architectural Gaps for Multi-Agent Coding Workflows:**
  - *No Semantic Code Property Graph (SCPG) Lenses:* Treats all nodes and edges uniformly; cannot isolate call graphs from def-use data flows, configuration bindings, or exception hierarchies.
  - *No Cross-Language Data & HTTP Boundary Bridges:* Cannot resolve TypeScript `fetch('/api/v1/users')` to Python `@app.get('/api/v1/users')`, nor track SQL table writes to Python reads.
  - *Namespace Collision Vulnerability:* Symbols sharing identical names (e.g. `next` in npm vs `next` in Python built-in) cause catastrophic graph bridging and traversal blowouts.
  - *No Token-Governed Context Compiler:* Queries return raw subgraphs or text summaries, without compiling focused, file-capped snippets (~40 lines) for immediate agent action.
  - *No Git Temporal Coupling:* Ignores version control history; cannot identify files that always change together despite having no direct static import edge.
  - *Flat In-Memory Storage:* NetworkX full-graph traversal scales poorly on large graphs without index acceleration (e.g. SQLite recursive CTEs).

---

## 4. RepoPeek Architectural Vision & Invariants

RepoPeek combines Graphify's local pipeline simplicity with compiler-grade static analysis and agent orchestration principles:

```
+---------------------------------------------------------------------------------------------------+
| REPOPEEK CORE INVARIANTS                                                                          |
|                                                                                                   |
| 1. Strict Context Budgeting:                                                                      |
|    Natural-language task compilation MUST produce <=4 files with ~40-line snippets (~1-2k tokens).|
|                                                                                                   |
| 2. Deterministic Ground Truth First (Tier 1 AST Fact Engine):                                     |
|    Static facts (calls, reads, writes, raises) are extracted deterministically without LLM.      |
|    LLM overlays are validated by an AST Fact Verifier before admission.                           |
|                                                                                                   |
| 3. Explicit Runtime Namespacing:                                                                  |
|    All entities are strictly prefixed by runtime domain (py:, ts:, sql:, sh:, npm:, py_builtin:)  |
|    to prevent cross-language graph pollution.                                                     |
|                                                                                                   |
| 4. Deterministic Multi-Lens Projections:                                                           |
|    9 focused graph projections (Module, Symbol, Call, Class, Data, Entity, Config, Process,       |
|    Exception) are materialized on demand from the canonical SCPG.                                 |
|                                                                                                   |
| 5. Dual-Layer Storage Engine:                                                                     |
|    Atomic, content-addressed JSON shards on disk + high-speed SQLite recursive CTE cache for      |
|    sub-millisecond reachability, blast-radius, and data-flow queries.                             |
|                                                                                                   |
| 6. Temporal Git Intelligence:                                                                     |
|    Commit history mined with 180-day exponential half-life decay synthesizes CO_CHANGED_WITH      |
|    graph edges, revealing architectural coupling invisible to static ASTs.                        |
+---------------------------------------------------------------------------------------------------+
```

---

## 5. Comprehensive Comparison Matrix: Baseline vs Target

| Feature Dimension | Graphify Baseline (`Reference/graphify`) | RepoPeek Target (`RepopeekV2`) |
|---|---|---|
| **Primary Objective** | Repository map & documentation graph | Actionable multi-agent context compiler & navigation map |
| **Parsing Engine** | Tree-sitter AST for ~40 languages | Polyglot substrate: Python stdlib AST, TS/JS Tree-sitter, SQLGlot, Shell, YAML/JSON |
| **Graph Model** | Single homogeneous NetworkX graph | Semantic Code Property Graph (SCPG) with 9 materialized lenses |
| **Lenses Supported** | None (single graph view with community colors) | 9 switchable lenses (`Module`, `Symbol`, `Call`, `Class`, `Data`, `Entity`, `Config`, `Process`, `Exception`) |
| **Cross-Language Bridges** | Generic file-level import stubs | HTTP boundary bridge (`:param` normalization), SQL table def-use, subprocess tracking |
| **Namespace Isolation** | Unnamespaced labels; subject to string collision | Strict runtime prefixing (`npm:`, `py_builtin:`, `py:`, `ts:`, `sql:`, `sh:`) |
| **Storage & Caching** | Flat `graph.json` + file mtime cache | Content-addressed JSON shards + SQLite recursive CTE cache |
| **Query Engine** | BFS/DFS text exploration, shortest path | Low-latency recursive queries: `lookup`, `neighbors`, `impact`, `data_trace`, `routes`, `co_changes` |
| **Git Intelligence** | Git commit stamp comparison | Temporal mining with 180-day exponential decay, `CO_CHANGED_WITH` probability matrix |
| **Semantic Summaries** | Single LLM pass over docs/code | 5-tier story cascade with deterministic AST Fact Verifier anti-hallucination guardrail |
| **Agent Context Packaging** | Full-report or raw subgraph text dump | Task-specific context compiler: strictly **≤4 files with ~40-line spans** (~1–2k tokens) |
| **Change Planning** | PR impact triage by touched communities | Risk-assessed step-by-step change plan engine with blast radius |
| **MCP Server Tools** | 10 tools oriented toward PR triage & graph query | 10 tools tailored for autonomous coding agents (`context`, `plan`, `impact`, `lookup`, etc.) |
| **Interactive Viewer** | Standalone D3 `graph.html` | Zero-dependency D3 viewer with 9 switchable lenses, glowing links, and blast-radius highlight |
| **Obsidian Vault Export** | Flat node notes + community notes | Obsidian vault with `.obsidian/` color groups, 9 lens tags, and bidirectional `[[wikilinks]]` |
| **Incremental Sync** | Polling file watch on code files | Zero-dependency stdlib watch daemon achieving **<50ms incremental sync** |

---

## 6. Success & Validation Metrics

RepoPeek development and verification will be governed by three golden benchmark scenarios:

1. **Golden Scenario 1: Multi-Language Blast Radius**
   - *Target:* Modifying an orchestrator function (`InvoiceParser.parse`) and a database entity (`table.invoices`).
   - *Requirement:* Accurately traverse upstream and downstream reachability across Python code, SQL queries, Shell scripts, and YAML configs within <50ms.
2. **Golden Scenario 2: Data Flow Traceability**
   - *Target:* Data entity tracing for SQL tables and configuration keys (`table.invoices`, `database.dialect`).
   - *Requirement:* Unambiguously separate write sites (`WRITES` from `INSERT`/`UPDATE`) from read sites (`READS` from `SELECT`/`config.get`).
3. **Golden Scenario 3: Context Pack Budget Adherence**
   - *Target:* Compiling context for complex feature requests or bug fixes.
   - *Requirement:* Context package strictly caps output at **≤4 files**, extracts **~40-line snippets**, delivers **1–2k tokens**, and achieves **≥85% fact coverage** without token overflow.
