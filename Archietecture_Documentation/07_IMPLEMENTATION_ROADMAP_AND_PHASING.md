# 07 - Implementation Roadmap & Verification Plan

## 1. Phased Implementation Roadmap

To systematically construct RepoPeek using the baseline architecture from Graphify while fulfilling all requirements in `Expectations/README.md` and maintaining **100% language parity (40+ languages, 103+ file extensions)**, the engineering effort is structured into **5 sequential phases**.

```
+----------------------------------------------------------------------------------------------------+
| 5-PHASE REPOPEEK IMPLEMENTATION ROADMAP                                                            |
|                                                                                                    |
|  [PHASE 1: Foundation & Full Polyglot Parsing Substrate (40+ Languages)]                           |
|  - Complete 40+ language extractor suite, 103+ extensions, Tree-sitter grammars, shebang dispatch.   |
|  - Universal namespace tagging (py:, ts:, go:, rs:, java:, c:, cs:, etc.), AST normalization.      |
|                                │                                                                   |
|                                ▼                                                                   |
|  [PHASE 2: Semantic Code Property Graph & 9 Materialized Lenses]                                  |
|  - Canonical SCPG builder, universal namespace isolation, Leiden clustering, 9 lens projections.   |
|                                │                                                                   |
|                                ▼                                                                   |
|  [PHASE 3: Cross-Language Bridges, Git Intelligence & Dual Storage Engine]                         |
|  - HTTP boundary bridge, SQL def-use bridge, SQLite recursive CTE cache, git temporal mining.      |
|                                │                                                                   |
|                                ▼                                                                   |
|  [PHASE 4: 5-Tier Story Cascade & Task Context Compiler]                                           |
|  - AST fact templates, SHA-256 cache, LLM summaries + Fact Verifier, <=4 files context compiler.   |
|                                │                                                                   |
|                                ▼                                                                   |
|  [PHASE 5: Full Ecosystem Suite, 11-Tool MCP Server, Visualizers & Golden Verification]            |
|  - 20+ platform installers, dual MCP transports, 11 tools, telemetry HUD, 9-lens D3, Obsidian.     |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Detailed Work Breakdown by Phase

### Phase 1: Foundation & Full Polyglot Parsing Substrate (40+ Languages)
**Objective:** Deliver deterministic, local AST fact extraction across all 40+ programming languages and 103+ file extensions supported by Graphify.

- [ ] **Task 1.1: Project Skeleton & Complete Polyglot Dependency Matrix**
  - Configure `pyproject.toml` with pinned base dependencies (`tree-sitter>=0.25,<0.26`, `tree-sitter-python`, `tree-sitter-javascript`, `tree-sitter-typescript`, `tree-sitter-go`, `tree-sitter-rust`, `tree-sitter-java`, `tree-sitter-groovy`, `tree-sitter-c`, `tree-sitter-cpp`, `tree-sitter-ruby`, `tree-sitter-c-sharp`, `tree-sitter-kotlin`, `tree-sitter-scala`, `tree-sitter-php`, `tree-sitter-swift`, `tree-sitter-lua`, `tree-sitter-zig`, `tree-sitter-powershell`, `tree-sitter-elixir`, `tree-sitter-objc`, `tree-sitter-julia`, `tree-sitter-verilog`, `tree-sitter-fortran`, `tree-sitter-bash`, `tree-sitter-json`).
  - Configure optional language extras matching Graphify: `sql`, `pascal`, `dm`, `terraform`, `ocaml`, `commonlisp`, `robot`, `vbnet`, `r`, `erlang`, `solidity`.
  - Establish modular package structure under `repopeek/`: `detect/`, `extractors/`, `parsers/`, `bridges/`, `lenses/`, `storage/`, `context/`, `serve/`, `cli/`.
- [ ] **Task 1.2: Repository Scanner, Extension Classifier & Shebang Dispatch (`repopeek.detect`)**
  - Implement file discovery honoring `.gitignore` and `.repopeekignore` with 103+ extension classifier (`CODE_EXTENSIONS`).
  - Implement shebang line interpreter dispatch (`_SHEBANG_DISPATCH`) for extensionless scripts (`python`, `bash`, `sh`, `node`, `ruby`, `lua`, `php`, `julia`, `Rscript`).
  - Implement safety resource caps: 50MB raw / 512MB decompressed zip screening for Office/PDFs; corpus threshold warnings (>500 files / >500k words).
- [ ] **Task 1.3: Polyglot Extractor Dispatch Engine (`repopeek.extract`)**
  - Integrate Graphify's multi-worker `ProcessPoolExecutor` with sequential fallback (`_safe_extract`) and recursion ceiling protection (`_RECURSION_LIMIT = 10_000`).
  - Implement complete `_DISPATCH` table mapping all 103+ extensions to their specialized extractors:
    - *Web / Fullstack:* Python, TypeScript, JavaScript, JSX, TSX, Vue, Svelte, Astro.
    - *Systems & Native:* Rust, Go, C, C++, CUDA, Metal, Zig.
    - *Enterprise & JVM:* Java, Groovy, Gradle, Kotlin, Scala, C#, VB.NET, Razor/Blazor, XAML, Solution/Project files.
    - *Apple Ecosystem:* Swift, Objective-C, Objective-C++.
    - *Scripting & Automation:* Ruby, PHP, Blade, Lua, Luau, PowerShell, Bash, Robot Framework, Terraform/HCL.
    - *Concurrent & Functional:* Elixir, Erlang, OCaml, Common Lisp, Dart.
    - *Scientific & Numeric:* R, Julia, Fortran (with CPP preprocessor).
    - *Legacy & Enterprise:* Pascal/Delphi/Lazarus, COBOL.
    - *Hardware & Blockchain:* Verilog/SystemVerilog, Solidity, Salesforce Apex, BYOND DM.
    - *Database & Data:* SQL (DDL + DML def-use), JSON configs, manifests (`package.json`, `Cargo.toml`, `pyproject.toml`).
- [ ] **Task 1.4: Universal Namespace Tagging & AST Normalization**
  - Wrap extractor outputs to guarantee canonical namespace prefixes across all entities (`py:`, `ts:`, `go:`, `rs:`, `java:`, `c:`, `cpp:`, `cs:`, `rb:`, `php:`, `kt:`, `swift:`, `lua:`, `zig:`, `sh:`, `ps:`, `ex:`, `erl:`, `dart:`, `r:`, `jl:`, `ml:`, `lisp:`, `f:`, `pas:`, `cbl:`, `apex:`, `sol:`, `v:`, `dm:`, `tf:`, `robot:`, `sql:`, `cfg:`, `doc:`, `npm:`, `pip:`, `cargo:`, `nuget:`, `gomod:`).
  - Ensure every node carries byte offsets (`start_byte`, `end_byte`), line numbers (`start_line`, `end_line`), docstrings, and def-use variables.
- [ ] **Task 1.5: Symbol Resolution & Type Linking Substrate**
  - Integrate Graphify's resolver registry (`resolver_registry.py`), cross-file import resolver, C++ declaration/definition merger (`_merge_decl_def_classes`), C# interface dispatch (`csharp_dispatch.py`), Swift protocol dispatch (`swift_dispatch.py`), Ruby member calls (`ruby_resolution.py`), and Pascal inherited calls (`pascal_resolution.py`).
- [ ] **Task 1.6: Polyglot Test Fixture Suite & Verification**
  - Author test fixtures across 25+ language families in `tests/fixtures/polyglot/`.
  - Validate fact extraction, line spans, byte offsets, and namespace isolation in `tests/test_parsers.py`.
- **Phase 1 Deliverable & Verification:** Passing polyglot extractor test suite validating zero crashes and accurate AST facts across all 40+ supported languages.

---

### Phase 2: Semantic Code Property Graph & 9 Materialized Lenses
**Objective:** Assemble extracted facts into a unified property graph with runtime namespace isolation and deterministic lens materialization.

- [ ] **Task 2.1: Canonical SCPG Builder (`repopeek.build`)**
  - Construct NetworkX property graph (`nx.DiGraph`) maintaining directed arc order.
  - Reify external dependencies and built-ins as typed stub nodes (`external=True`).
- [ ] **Task 2.2: Universal Namespace Isolation Protocol**
  - Enforce explicit runtime prefixes across all 40+ languages.
  - Validate that raw string matches (e.g. `next` in React vs `next` in Python vs `Next` in C#) never bridge across disconnected language trees.
- [ ] **Task 2.3: Community Detection Engine (`repopeek.cluster`)**
  - Implement Leiden community clustering via `graspologic_native` with Louvain fallback.
  - Generate deterministic, LLM-free community labels based on internal high-degree symbols.
- [ ] **Task 2.4: 9 Materialized Lenses Engine (`repopeek.lenses`)**
  - Implement on-demand sub-projection materializer for the 9 lenses: `Module`, `Symbol`, `Call`, `Class`, `Data`, `Entity`, `Config`, `Process`, `Exception`.
  - Store lens bitmasks on nodes and edges for instant sub-graph filtering across all 40+ languages.
- **Phase 2 Deliverable & Verification:** Graph build suite (`tests/test_graph_build.py`) verifying graph assembly, community stability, and lens projection accuracy.

---

### Phase 3: Cross-Language Bridges, Git Intelligence & Dual Storage Engine
**Objective:** Connect language trees, mine temporal co-changes, and implement sub-millisecond SQLite query caching.

- [ ] **Task 3.1: Cross-Language HTTP Boundary Bridge (`repopeek.bridges.http`)**
  - Implement wildcard path parameter normalizer (`:param`).
  - Match TypeScript/JS/Dart/Swift API calls to Python/Go/Java/C#/Ruby route handlers; synthesize `INVOKES` edges with confidence 0.75.
- [ ] **Task 3.2: SQL Data Def-Use Bridge (`repopeek.bridges.sql`)**
  - Connect application code database operations across all supported backend languages to SQL schema tables with `READS` and `WRITES` edges.
- [ ] **Task 3.3: Git Temporal Miner (`repopeek.temporal.miner`)**
  - Mine git commit history using exponential decay with 180-day half-life.
  - Compute conditional co-change probability matrix $P(B \mid A)$ and synthesize `CO_CHANGED_WITH` edges.
- [ ] **Task 3.4: Dual Storage Engine (`repopeek.storage`)**
  - Implement content-addressed atomic JSON sharder under `.repopeek/shards/`.
  - Implement SQLite recursive CTE cache schema (`.repopeek/cache.db`) with indexes.
  - Author recursive CTE queries for upstream callers and downstream blast radius reachability.
- [ ] **Task 3.5: Incremental Watch Daemon (`repopeek.watch`)**
  - Implement debounced filesystem change tracker with sub-50ms delta invalidation and SQLite cache updates.
- **Phase 3 Deliverable & Verification:** Bridge and storage test suite (`tests/test_bridges.py`, `tests/test_storage.py`) validating <50ms watch sync and CTE recursive traversal.

---

### Phase 4: 5-Tier Story Cascade & Task Context Compiler
**Objective:** Deliver token-budgeted context packages (≤4 files, ~40 lines) with anti-hallucination verification.

- [ ] **Task 4.1: Deterministic AST Fact Templates (Tier 1)**
  - Implement zero-cost Markdown fact generator from AST properties across all languages.
- [ ] **Task 4.2: Content-Hash Story Cache (Tier 2)**
  - Implement disk cache keyed by symbol content SHA-256.
- [ ] **Task 4.3: Cheap-Model Structured Summarizer & Rollup (Tiers 3 & 4)**
  - Implement structured JSON summary generation via Groq API (`qwen3.8-27b`) or local Ollama.
  - Implement bottom-up hierarchical rollup: Symbol -> Class -> File -> Community.
- [ ] **Task 4.4: AST Fact Verifier Guardrail (Tier 5)**
  - Implement claim verifier checking extracted claims (`calls`, `writes`, `raises`) against AST ground truth.
  - Implement automatic fallback to Tier 1 on verification failure.
- [ ] **Task 4.5: Context Compiler (`repopeek.context.compiler`)**
  - Implement task-driven context pack compiler: strictly **≤4 files cap**, **~40-line snippets**, **~1–2k tokens**.
  - Implement 3-tier progressive disclosure (Level 1 Orientation, Level 2 Actionable Pack, Level 3 Deep Plan).
- [ ] **Task 4.6: Change Plan Engine (`repopeek.context.planner`)**
  - Formulate step-by-step risk-assessed implementation plans with blast radius and test recommendations.
- **Phase 4 Deliverable & Verification:** Context compiler test suite (`tests/test_compiler.py`) proving compliance with the 4-file cap and token budget limits.

---

### Phase 5: Ecosystem Suite, 11-Tool MCP Server, Visualizers & Golden Verification
**Objective:** Deliver 100% ecosystem parity with Graphify (20+ AI assistant platforms, dual MCP transports, full exporter suite, PR triage) plus RepoPeek's 11 MCP tools, Telemetry HUD, and Golden Scenarios.

- [ ] **Task 5.1: 11-Tool Dual-Transport MCP Server (`repopeek.serve`)**
  - Implement JSON-RPC 2.0 stdio server supporting both MCP 1.x and 2.x specifications.
  - Implement Streamable HTTP ASGI server (`serve_http`) with SSE and API key gate.
  - Wire all 11 tools: `repopeek_lookup`, `repopeek_neighbors`, `repopeek_impact`, `repopeek_data_trace`, `repopeek_context_pack`, `repopeek_context`, `repopeek_plan`, `repopeek_routes`, `repopeek_co_changes`, `repopeek_resolve`, `repopeek_savings`.
- [ ] **Task 5.2: Telemetry & Savings Scorecard HUD (`repopeek.telemetry`)**
  - Implement counterfactual baseline tracking (unconstrained blast radius vs RepoPeek compile).
  - Compute tokens saved, files avoided, cache hit rate, and dollar cost reduction ($3/M tokens input baseline).
  - Implement in-line context scorecards and CLI/web HUDs.
- [ ] **Task 5.3: 20+ AI Platform Installer & Hook Guards (`repopeek.install`)**
  - Port Graphify's multi-platform installer supporting 20+ assistants (Claude Code, Cursor, Codex, Gemini, Antigravity, Hermes, Copilot, Trae, etc.).
  - Implement `PreToolUse` hook guards (`hook-guard`), strict read denial mode (`--strict`), and instruction generators (`AGENTS.md`, `.cursor/rules/`).
- [ ] **Task 5.4: PR Review, Conflict & Blast Triage Suite (`repopeek.prs`)**
  - Implement GitHub PR integration: `prs`, `prs <id>`, `prs --triage`, and `prs --conflicts`.
  - Calculate graph blast radius and touched communities on PR diffs.
- [ ] **Task 5.5: Full Visualization & Knowledge Exporter Suite**
  - Construct standalone D3 force viewer (`graph.html`) with 9-lens toolbar, glowing links, and Savings HUD.
  - Deliver Collapsible Tree HTML (`GRAPH_TREE.html`) and Callflow Mermaid HTML.
  - Deliver native Obsidian Vault exporter (`--export-obsidian`) with 9-lens color groupings.
  - Support SVG, GraphML, Markdown Wiki, and Neo4j/FalkorDB push.
- [ ] **Task 5.6: Golden Scenarios End-to-End Validation**
  - Validate **Golden Scenario 1 (Multi-Language Blast Radius):** Modifying `InvoiceParser.parse` and `table.invoices` traces across Python, SQL, Shell, and YAML in <50ms.
  - Validate **Golden Scenario 2 (Data Flow Traceability):** Separate writer nodes (`INSERT`) from reader nodes (`SELECT`) for `table.invoices` and `database.dialect`.
  - Validate **Golden Scenario 3 (Context Pack Budget):** Task compilation strictly honors **≤4 files cap**, **~40-line snippets**, and **1–2k token budget**.
- **Phase 5 Deliverable & Verification:** Full passing test suite (`pytest tests`) including `tests/test_golden_scenarios.py` with 100% assertion pass rate.

---

## 3. Dependency & Milestone Schedule

```
Week 1-2: Phase 1 (Full 40+ Language Polyglot Parsers, 103+ Extensions, Universal Namespace Tagging)
Week 3:   Phase 2 (Canonical SCPG, Universal Namespace Isolation, Leiden Clustering, 9 Lenses)
Week 4-5: Phase 3 (HTTP Boundary Bridge, SQL Bridge, SQLite Recursive CTEs, Git Miner, Watch Daemon)
Week 6:   Phase 4 (5-Tier Story Cascade, Fact Verifier Guardrail, Context Compiler, Change Planner)
Week 7:   Phase 5 (11-Tool MCP Server, Telemetry Scoreboard, 20+ Platforms, D3 Web Viewer, Obsidian, Golden Scenarios)
```
