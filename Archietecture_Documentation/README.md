# RepoPeek Architecture Documentation Suite

## Overview

This directory contains the comprehensive architectural specification and implementation blueprint for **RepoPeek**, a multi-agent Semantic Code Property Graph (SCPG) intelligence engine.

RepoPeek builds upon the battle-tested, local-first AST pipeline baseline established by **Graphify**, evolving it into an agent-centric code intelligence engine tailored for LLM coding workflows, deterministic context budgeting (≤4 files, ~40-line spans), multi-lens projections, 40+ language AST extraction (103+ file extensions), cross-language boundary bridges, git temporal co-change mining, quantifiable ROI telemetry, and an 11-tool dual-transport MCP server.

---

## Document Index

| Document | Title | Focus & Core Content |
|---|---|---|
| [01_EXECUTIVE_SUMMARY_AND_VISION.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/01_EXECUTIVE_SUMMARY_AND_VISION.md) | Executive Summary & Vision | Strategic vision, comparison matrix between Graphify baseline and RepoPeek expectations, core design invariants, and success metrics. |
| [02_SYSTEM_ARCHITECTURE_AND_PIPELINE.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/02_SYSTEM_ARCHITECTURE_AND_PIPELINE.md) | System Architecture & Pipeline | End-to-end processing pipeline (`detect` -> `extract` -> `bridge` -> `build` -> `cluster` -> `materialize_lenses` -> `index` -> `serve`), entity lifecycle, and global node/edge schemas. |
| [03_PARSING_BRIDGES_AND_LENS_SPECIFICATION.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/03_PARSING_BRIDGES_AND_LENS_SPECIFICATION.md) | Polyglot Parsers (40+ Languages), Bridges & 9 Lenses | Polyglot substrate covering 40+ languages / 103+ extensions, shebang dispatch, cross-language HTTP/SQL/Subprocess bridges, universal namespace isolation, and 9 deterministic lens definitions. |
| [04_STORAGE_INDEXING_AND_GIT_INTELLIGENCE.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/04_STORAGE_INDEXING_AND_GIT_INTELLIGENCE.md) | Storage, Indexing & Git Intelligence | Content-addressed JSON shards, SQLite recursive CTE graph cache, git temporal mining (half-life exponential decay, conditional co-change matrix), and <50ms watch daemon. |
| [05_STORY_CASCADE_AND_CONTEXT_COMPILER.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/05_STORY_CASCADE_AND_CONTEXT_COMPILER.md) | 5-Tier Story Cascade & Context Compiler | 5-tier semantic aggregation, AST fact verifier guardrail, task context compiler (≤4 files, ~40-line snippets, token budget governor), and risk-assessed change plan engine. |
| [06_MCP_SERVER_CLI_AND_INTERFACES.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/06_MCP_SERVER_CLI_AND_INTERFACES.md) | MCP Server, CLI & Visualizers | 11 MCP tools reference, unified CLI command surface, interactive D3 Obsidian-style force-directed web viewer (9 lenses), and native Obsidian vault exporter. |
| [07_IMPLEMENTATION_ROADMAP_AND_PHASING.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/07_IMPLEMENTATION_ROADMAP_AND_PHASING.md) | Implementation Roadmap & Verification | Phase-by-phase implementation schedule (Phases 1-5), full 40+ language rollout, task work breakdown, dependency graph, testing protocols, and verification against Golden Scenarios. |
| [08_GRAPHIFY_HYBRID_INTEGRATION_BLUEPRINT.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/08_GRAPHIFY_HYBRID_INTEGRATION_BLUEPRINT.md) | Graphify Hybrid Integration Blueprint | Detailed design for reusing Graphify's engine directly (40+ language extractors, _DISPATCH table) and adding the RepoPeek feature set and 11-tool MCP server as an additive overlay. |
| [09_TELEMETRY_SAVINGS_AND_ROI_SCOREBOARD.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/09_TELEMETRY_SAVINGS_AND_ROI_SCOREBOARD.md) | Telemetry, Savings & ROI Scoreboard Engine | Context efficiency tracking, tokens/files saved counterfactual formulation, CLI scoreboard, and web viewer HUD. |
| [10_COMPREHENSIVE_PLATFORM_AND_ECOSYSTEM_SUPPORT.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/10_COMPREHENSIVE_PLATFORM_AND_ECOSYSTEM_SUPPORT.md) | Comprehensive Platform & Ecosystem Support | Support matrix for 20+ AI platforms, 40+ language grammars, multi-format exporters, dual MCP transports, and PR review triage. |

---

## Architectural Baseline vs Target Comparison

```
+---------------------------------------------------------------------------------------------------+
| GRAPHIFY (Baseline Foundation)                                                                    |
| - Pipeline: detect -> extract -> build -> cluster -> analyze -> report -> export                  |
| - Tree-sitter syntactic extraction across 40+ languages (103+ extensions)                         |
| - In-memory NetworkX graph + flat graph.json export                                               |
| - Leiden / Louvain community clustering                                                           |
| - Text BFS/DFS queries + D3 graph.html + Obsidian vault export                                    |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v  [Evolved & Re-Architected]
+---------------------------------------------------------------------------------------------------+
| REPOPEEK (Target Multi-Agent Code Intelligence Engine)                                            |
| - Semantic Code Property Graph (SCPG) with 9 deterministic materialized lenses                    |
| - Polyglot data-flow tracking (READS, WRITES, INVOKES) across 40+ languages & 103+ extensions     |
| - HTTP Boundary Bridge (:param normalization) connecting frontend clients to backend routes     |
| - Universal runtime namespace isolation preventing cross-language graph collision explosions     |
| - SQLite recursive CTE cache + content-addressed atomic JSON sharding                             |
| - Git temporal intelligence mining (180-day exponential half-life, CO_CHANGED_WITH edges)         |
| - 5-Tier story cascade with deterministic AST Fact Verifier anti-hallucination guardrail          |
| - Context Compiler strictly delivering <=4 files with ~40-line spans (~1-2k tokens)               |
| - Dual-Transport JSON-RPC MCP Server (stdio + HTTP ASGI) exposing 11 specialized agent tools     |
| - Telemetry & Savings Scorecard HUD proving quantifiable token, file, and cost reduction          |
| - Zero-dependency incremental watch daemon (<50ms sync)                                           |
+---------------------------------------------------------------------------------------------------+
```
