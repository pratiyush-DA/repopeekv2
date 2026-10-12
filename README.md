# RepoPeek V2

Autonomous Repository Intelligence Engine & Semantic Code Property Graph (SCPG) for AI Coding Agents.

RepoPeek compiles polyglot codebases into deterministic sub-graphs and token-governed context packages strictly bounded by **<=4 files with ~40-line spans** (~1-2k tokens). By eliminating unconstrained repo-wide file dumping, RepoPeek reduces AI agent context waste by up to 85% while providing mathematically verified blast radius analysis, cross-language bridges, git temporal intelligence, and an automated 16-tool Model Context Protocol (MCP) server.

---

## Architecture Pipeline

```
+----------------------------------------------------------------------------------------------------+
|                                    REPOPEEK V2 PIPELINE                                            |
|                                                                                                    |
|  [Workspace Files] (40+ Languages / 103+ Extensions / Shebang Dispatch)                           |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Polyglot AST Extractors] ──> NodeRecord & EdgeRecord Tuples                                      |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Cross-Language Bridges]  ──> HTTP Routes (:param) | SQL Def-Use | Subprocess | Config Keys        |
|         │                                                                                          |
|         ▼                                                                                          |
|  [DiGraph Assembly]        ──> Universal Namespace Isolation (py:, ts:, go:, rs:, java:, etc.)    |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Leiden Clustering]       ──> Hierarchical Community Detection & Semantic Boundaries              |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Git Temporal Mining]     ──> 180-Day Half-Life Decay & CO_CHANGED_WITH Coupling (P >= 0.25)      |
|         │                                                                                          |
|         ▼                                                                                          |
|  [9 Materialized Lenses]   ──> Module, Symbol, Call, Class, Data, Entity, Config, Process, Except  |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Dual Storage Engine]     ──> Content-Addressed JSON Shards + SQLite Recursive CTE Graph Cache    |
|         │                                                                                          |
|         ├───► 16-Tool Dual-Transport MCP Server (Stdio JSON-RPC + Streamable HTTP ASGI)            |
|         ├───► Unified CLI (Context Compiler, Blast Radius, PR Triage, Diagnostics, Cycles)         |
|         ├───► Incremental Watch Daemon (<50ms In-Memory & SQLite Sync)                             |
|         └───► Multi-Format Exporters (D3 Canvas, Obsidian Vault, Callflow, Wiki, Cypher, GraphML)   |
+----------------------------------------------------------------------------------------------------+
```

---

## Key Capabilities

1. **100% Polyglot Support (40+ Languages, 103+ File Extensions):** Tree-sitter and specialized AST fact extraction across Python, TypeScript, JavaScript, Go, Rust, Java, C/C++, C#, Kotlin, Swift, Scala, PHP, Ruby, Lua, Zig, PowerShell, Bash, Elixir, Erlang, Dart, R, Julia, OCaml, Common Lisp, Fortran, Pascal, COBOL, Solidity, Verilog, Apex, Terraform, and SQL. Extensionless scripts are classified dynamically via shebang interpreter dispatch.
2. **Task-Driven Context Compiler (<=4 Files Cap):** Progressive disclosure of task context strictly bounded by a 4-file cap and ~40-line character-offset snippets (~1-2k tokens), with three progressive disclosure levels (Level 1: Orientation, Level 2: Focus Pack, Level 3: Deep Risk Plan).
3. **Mathematical Blast Radius & Reachability:** Upstream impact traversal (`"If I edit X, what breaks?"`) and downstream reachability analysis across call hierarchies, type inheritance, and database tables.
4. **Cross-Language Boundary Bridges:**
   - **HTTP Boundary Bridge:** Maps frontend client API calls (`fetch`, `axios`) to backend route controllers via `:param` path normalization.
   - **SQL Def-Use Bridge:** Maps database queries to application symbols using `READS` and `WRITES` edges across tables and views.
   - **Process & Config Bridges:** Binds subprocess invocations and configuration keys across language barriers.
5. **Universal Namespace Isolation:** Strict runtime prefixes (`py:`, `ts:`, `go:`, `rs:`, `java:`, etc.) prevent symbol collision explosions in polyglot monorepos.
6. **9 Deterministic Materialized Lenses:** On-demand sub-projections for `Module`, `Symbol`, `Call`, `Class`, `Data`, `Entity`, `Config`, `Process`, and `Exception`.
7. **Git Temporal Intelligence:** 180-day exponential half-life decay mining that uncovers hidden co-change matrices and `CO_CHANGED_WITH` edges (P >= 0.25).
8. **16-Tool Dual-Transport MCP Server:** Native JSON-RPC stdio and Streamable HTTP ASGI transports supporting 20+ AI assistant platforms (Claude Code, Cursor, Antigravity IDE, Claude Desktop, Copilot, Codex, etc.).
9. **Automated AI Assistant Installer:** Single-command setup for Claude Code, Cursor, Antigravity IDE, and GitHub Copilot.
10. **Pull Request Blast Radius Review:** Automated branch diff comparison against base branch, reporting modified nodes, affected external callers, and touched architectural communities.
11. **Experiential Memory & Reflection:** Records task Q&A outcomes (`useful`, `dead_end`, `corrected`) and synthesizes time-decayed engineering lessons into `docs/LESSONS.md`.
12. **Multi-Repository Global Graph:** Centralized knowledge graph registry (`~/.repopeek/global-graph.json`) enabling cross-repository discovery and traversal.
13. **Sub-50ms Incremental Watch Daemon:** Fast filesystem stat checks and SHA-256 caching for real-time in-memory and SQLite index synchronization.
14. **Dual Storage Engine:** Content-addressed atomic JSON sharding (`.repopeek/shards/`) combined with SQLite recursive CTE indexing (`.repopeek/index.sqlite`) featuring anti-shrink protection guards.
15. **Quantifiable ROI & Telemetry Scoreboard:** Real-time tracking of token savings, avoided file reads, and dollar cost reduction relative to an unconstrained blast-radius baseline.
16. **Multi-Format Visualizers & Exporters:** Standalone interactive D3 canvas viewer (`repopeek_graph.html`), Obsidian Markdown vault export with wikilinks, Obsidian `.canvas` export, Mermaid callflow HTML, markdown wiki, Neo4j/FalkorDB Cypher DDL, GraphML, and vector SVG.

---

## Installation

### Global Installation via pipx or uv

```bash
# Global installation via pipx
pipx install git+https://github.com/pratiyush-DA/repopeekv2.git

# Or via uv
uv tool install git+https://github.com/pratiyush-DA/repopeekv2.git
```

### Local Development Installation

```bash
# Clone the repository
git clone https://github.com/pratiyush-DA/repopeekv2.git
cd repopeekv2

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with all optional dependencies (MCP, watch daemon, polyglot grammars, clustering)
pip install -e ".[all]"
```

#### Optional Dependency Extras

- `mcp`: MCP stdio and Starlette HTTP ASGI server dependencies (`mcp>=1,<3`, `starlette>=1.3.1,<2`).
- `watch`: Real-time filesystem watcher (`watchdog`).
- `cluster`: Graph clustering algorithms (`graspologic` / `graspologic-native`).
- `polyglot`: Extended tree-sitter grammars (Go, Rust, Java, C/C++, Ruby, C#, Kotlin, Scala, PHP, Swift, Lua, Zig, PowerShell, Elixir, Julia, Fortran, Bash, SQL, HCL).
- `all`: Installs all optional extras above.

---

## Automated AI Assistant Setup

RepoPeek provides a built-in installer to configure AI coding assistants with MCP definitions and efficiency rules in one command:

```bash
# Configure all supported platforms at once
repopeek install --platform all

# Or configure a specific platform
repopeek install --platform claude-code   # Generates .mcp.json
repopeek install --platform cursor        # Generates .cursor/mcp.json and .cursor/rules/repopeek.mdc
repopeek install --platform antigravity   # Generates .agents/rules/repopeek.md
repopeek install --platform copilot       # Generates .github/copilot-instructions.md
```

### Manual MCP Server Configuration

To configure RepoPeek manually in an assistant's MCP configuration file (e.g. `mcp_config.json`, `.cursor/mcp.json`, or `claude_desktop_config.json`):

#### Stdio Transport

```json
{
  "mcpServers": {
    "repopeek": {
      "command": "repopeek",
      "args": [
        "--serve-mcp",
        "--repo-path",
        "/absolute/path/to/target-repo"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

#### HTTP ASGI Transport

```bash
# Launch HTTP ASGI server with API key
repopeek --serve-http --host 127.0.0.1 --port 8080 --api-key my-secret-key
```

```json
{
  "mcpServers": {
    "repopeek": {
      "url": "http://127.0.0.1:8080/mcp",
      "headers": {
        "Authorization": "Bearer my-secret-key"
      }
    }
  }
}
```

---

## 16-Tool MCP Server Reference

RepoPeek exposes 16 specialized tools to AI coding agents:

| Tool Name | Parameters | Description & Agent Workflow |
|---|---|---|
| `repopeek_lookup` | `query` (str) | Looks up a symbol or entity by name or ID. Returns formatted Markdown fact card with file location, line range, parameters, return type, and docstrings. |
| `repopeek_neighbors` | `query` (str), `relation_filter` (str?) | Inspects immediate 1-hop inbound and outbound edges for direct callers, callees, and mutations. |
| `repopeek_impact` | `target` (str), `max_depth` (int=3), `direction` (str="both") | Calculates blast radius (`upstream`, `downstream`, or `both`) to determine what breaks before editing code. |
| `repopeek_data_trace` | `query` (str) | Traces state def-use: identifies all writers and readers of a table, entity, or state variable across SQL and application code. |
| `repopeek_context_pack` | `targets` (list[str]), `token_budget` (int=2000) | Generates a budget-governed pack for known symbol IDs with zero fluff and exact line spans. |
| `repopeek_context` | `task` (str), `budget` (int=2000), `level` (int=2) | Compiles a natural-language task into focused **<=4 files with ~40-line snippets**, constraints, affected tests, and an efficiency scorecard. |
| `repopeek_plan` | `task` (str) | Formulates a step-by-step engineering plan with risk levels, affected callers, and test verification recommendations. |
| `repopeek_routes` | *(none)* | Lists detected cross-language HTTP routes, matching client API calls (`fetch`/`axios`) to backend route handlers. |
| `repopeek_co_changes` | `target` (str) | Surfaces files that temporally change together in git history (P >= 0.25) despite lacking direct static import links. |
| `repopeek_resolve` | `task` (str) | Disambiguates and ranks symbol candidates matching a natural-language description. |
| `repopeek_savings` | `timeframe` (str="current_session") | Presents quantifiable token, file-fetching, and dollar cost savings compared to unconstrained raw-repo exploration. |
| `repopeek_path` | `source` (str), `target` (str), `directed` (bool=false) | Finds the shortest path between source and target symbols with hop-by-hop relationship descriptions. |
| `repopeek_explain` | `query` (str) | Generates an exhaustive architectural breakdown of a symbol node, including connectivity, degree, lenses, and community. |
| `repopeek_query` | `question` (str), `mode` (str="bfs"), `budget_tokens` (int=1500) | Performs natural-language BFS or DFS graph traversal expanded across node vocabulary within a token budget. |
| `repopeek_diagnose` | *(none)* | Audits graph integrity and returns a health diagnostic report with edge distributions and anomalies. |
| `repopeek_cycles` | `max_cycles` (int=20) | Detects circular import and dependency cycles across the codebase. |

---

## Unified Command Line Interface (CLI)

The `repopeek` command provides comprehensive repository indexing, query, lifecycle, and export capabilities.

### 1. Indexing & Live Synchronization

```bash
# Index current repository into .repopeek/
repopeek --repo-path .

# Deterministic offline indexing (Zero LLM)
repopeek --repo-path . --offline

# Specify custom cache directory
repopeek --repo-path . --output-dir ./output

# Start incremental watch daemon (<50ms sync on file changes)
repopeek --repo-path . --watch

# Bypass anti-shrink protection guard during re-indexing
repopeek --repo-path . --force
```

### 2. Instant Graph Queries & Navigation

```bash
# Look up atomic symbol fact card
repopeek --lookup "InvoiceParser.parse"

# Inspect immediate 1-hop inbound and outbound neighbors
repopeek --neighbors "DualStorageEngine"

# Calculate upstream blast radius tree (max depth 3)
repopeek --impact "table.invoices" --depth 3

# Trace state def-use (who writes and reads entity X)
repopeek --trace "table.users"

# Compile focused <=4 files context package for a coding task
repopeek --context "add customer discount tier to billing pipeline" --level 2

# Generate risk-assessed step-by-step engineering plan
repopeek --plan "refactor auth token validation to use asymmetric keys"

# List detected cross-language HTTP routes
repopeek --routes

# Surface git temporal co-changes for a file or symbol
repopeek --co-changes "repopeek/storage.py"

# Find shortest path between two symbols
repopeek --path "extract_file" "query_upstream_blast_radius"

# Generate exhaustive technical explanation of a symbol
repopeek --explain "ContextCompiler"

# Natural-language graph search (BFS or DFS)
repopeek --query "How does HTTP route bridge match client endpoints?" --mode bfs

# Audit graph health and integrity
repopeek --diagnose

# Detect circular dependency or import cycles
repopeek --cycles
```

### 3. Git Lifecycle Integration & PR Review Triage

```bash
# Install git hooks (post-commit, post-checkout) and union merge driver
repopeek --hook install

# Check status of installed git hooks
repopeek --hook status

# Uninstall git hooks
repopeek --hook uninstall

# Analyze branch PR impact and blast radius against base branch
repopeek --prs --base main
```

### 4. Experiential Learning & Memory Reflection

```bash
# Save an experiential task outcome
repopeek --save-result "How to handle tree-sitter node spans?" "Use byte offsets with utf-8 decoding" useful

# Synthesize stored memories into docs/LESSONS.md with 30-day time decay
repopeek --reflect
```

### 5. Multi-Repository Global Graph Registry

```bash
# List all registered repositories in the global graph
repopeek --global-cmd list

# Display user-global graph storage path (~/.repopeek/global-graph.json)
repopeek --global-cmd path
```

### 6. Interactive Visualizers & Exporters

```bash
# Generate standalone interactive D3 HTML graph viewer (.repopeek/repopeek_graph.html)
repopeek --view

# Serve interactive graph viewer on a local web server (default port: 8080)
repopeek --serve --port 8080

# Export code property graph as an Obsidian Markdown vault with [[wikilinks]]
repopeek --export-obsidian ./my_obsidian_vault

# Export Obsidian .canvas visual graph
repopeek --export-canvas ./my_obsidian_vault/architecture.canvas

# Export Mermaid callflow HTML report
repopeek --export-callflow ./docs/callflow.html

# Export agent-crawlable markdown wiki
repopeek --export-wiki ./docs/wiki

# Export Neo4j / FalkorDB Cypher DDL and upsert statements
repopeek --export-cypher ./exports/repopeek.cypher

# Export standard GraphML (for Gephi, yEd)
repopeek --export-graphml ./exports/repopeek.graphml

# Export vector SVG diagram
repopeek --export-svg ./exports/repopeek.svg
```

### 7. Telemetry & ROI Savings Scoreboard

RepoPeek tracks context delivered to AI agents and computes the quantifiable token, file-fetch, and dollar savings achieved relative to an unconstrained blast-radius baseline:

```bash
# Display quantifiable savings HUD
repopeek --savings
```

Example Scorecard Output:

```
+----------------------------------------------------------------------------------------------------+
| REPOPEEK CONTEXT EFFICIENCY SCORECARD                                                              |
| Task: add customer discount tier to billing pipeline                                               |
| Files Delivered: 3 / 4 cap (Baseline: 24 files)                                                    |
| Tokens Delivered: 1,420 (Baseline: 19,850 tokens)                                                  |
| Context Reduction: 92.8%                                                                           |
| Estimated Cost Saved: $0.276 (Session Total: $3.42)                                                |
+----------------------------------------------------------------------------------------------------+
```

---

## 9 Deterministic Materialized Lenses

RepoPeek projects 9 focused sub-graphs from the unified Semantic Code Property Graph:

1. **Module Lens:** High-level package and module hierarchy, directory organization, and package dependencies.
2. **Symbol Lens:** Class, struct, interface, function, and method definitions with signatures and docstrings.
3. **Call Lens:** Direct call graph (`CALLS`, `INVOKES`) mapping execution flow between functions and methods.
4. **Class Lens:** Type inheritance (`INHERITS_FROM`, `IMPLEMENTS`) and polymorphic interface structures.
5. **Data Lens:** Variable and state definition-use chains (`READS`, `WRITES`, `MUTATES`).
6. **Entity Lens:** Database models, ORM mappings, tables, views, and persistence schemas.
7. **Config Lens:** Environment variables, YAML/JSON settings, and application configuration bindings.
8. **Process Lens:** CLI invocations, subprocess triggers, background tasks, and event subscriptions.
9. **Exception Lens:** Error definitions, `RAISES` relationships, and exception handling catch sites.

---

## Architecture Documentation Suite

Detailed architectural specifications and implementation blueprints are located in [Archietecture_Documentation/](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/):

- [01_EXECUTIVE_SUMMARY_AND_VISION.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/01_EXECUTIVE_SUMMARY_AND_VISION.md): Strategic vision, baseline comparison, design invariants, and success metrics.
- [02_SYSTEM_ARCHITECTURE_AND_PIPELINE.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/02_SYSTEM_ARCHITECTURE_AND_PIPELINE.md): End-to-end processing pipeline, entity lifecycle, and node/edge schemas.
- [03_PARSING_BRIDGES_AND_LENS_SPECIFICATION.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/03_PARSING_BRIDGES_AND_LENS_SPECIFICATION.md): Polyglot substrate (40+ languages / 103+ extensions), shebang dispatch, cross-language bridges, and 9 lens definitions.
- [04_STORAGE_INDEXING_AND_GIT_INTELLIGENCE.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/04_STORAGE_INDEXING_AND_GIT_INTELLIGENCE.md): Content-addressed JSON shards, SQLite recursive CTE cache, git temporal mining, and <50ms watch daemon.
- [05_STORY_CASCADE_AND_CONTEXT_COMPILER.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/05_STORY_CASCADE_AND_CONTEXT_COMPILER.md): 5-tier story cascade, AST fact verifier guardrail, context compiler (<=4 files), and change plan engine.
- [06_MCP_SERVER_CLI_AND_INTERFACES.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/06_MCP_SERVER_CLI_AND_INTERFACES.md): 16 MCP tools reference, unified CLI command surface, D3 web viewer, and Obsidian vault exporter.
- [07_IMPLEMENTATION_ROADMAP_AND_PHASING.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/07_IMPLEMENTATION_ROADMAP_AND_PHASING.md): Phase-by-phase implementation schedule, task breakdown, and testing protocols.
- [08_GRAPHIFY_HYBRID_INTEGRATION_BLUEPRINT.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/08_GRAPHIFY_HYBRID_INTEGRATION_BLUEPRINT.md): Architecture for hybrid integration with Graphify's extractor table.
- [09_TELEMETRY_SAVINGS_AND_ROI_SCOREBOARD.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/09_TELEMETRY_SAVINGS_AND_ROI_SCOREBOARD.md): Telemetry formula, context savings measurement, CLI scoreboard, and HUD rendering.
- [10_COMPREHENSIVE_PLATFORM_AND_ECOSYSTEM_SUPPORT.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/10_COMPREHENSIVE_PLATFORM_AND_ECOSYSTEM_SUPPORT.md): Support matrix for 20+ AI platforms, dual transports, and PR review triage.
- [11_CODING_ARCHITECTURE_AND_DESIGN_PATTERNS.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/11_CODING_ARCHITECTURE_AND_DESIGN_PATTERNS.md): Three-tier engineering governance (Ponytail simplicity, Agent-Skills SDLC, Graphify local-first robustness).

---

## Notion Customer Portal

Customer setup guides, usage examples, and full feature specifications are published on Notion:
- [REPOPEEK_ARC:V2 on Notion](https://app.notion.com/p/REPOPEEK_ARC-V2-3f40f043dc1a81179f18d5ed02deec2e)

---

## Verification & Testing

RepoPeek is validated with an automated test suite covering all modules:

```bash
# Run full test suite
python -m pytest

# Run tests with verbose output
python -m pytest -v
```

All 68 unit tests verify parsing dispatch, cross-language bridges, context compilation, dual storage engines, 16 MCP tool endpoints, HTTP ASGI transport, git temporal mining, PR blast radius calculation, and graph exporters.

---

## License

Apache-2.0
