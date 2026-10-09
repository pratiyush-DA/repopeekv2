# RepoPeek V2

Autonomous Repository Intelligence Engine & Semantic Code Property Graph (SCPG) for AI Coding Agents.

RepoPeek compiles entire polyglot codebases into deterministic sub-graphs and token-governed context packages (strictly **<=4 files with ~40-line spans**, ~1-2k tokens), eliminating blind repo-wide file dumping and reducing AI agent context waste by up to 85%.

---

## Key Capabilities

1. **100% Polyglot Support (40+ Languages, 103+ File Extensions):** Tree-sitter and specialized AST fact extraction across Python, TypeScript, JavaScript, Go, Rust, Java, C/C++, C#, Kotlin, Swift, Scala, PHP, Ruby, Lua, Zig, PowerShell, Bash, Elixir, Erlang, Dart, R, Julia, OCaml, Common Lisp, Fortran, Pascal, COBOL, Solidity, Verilog, Apex, Terraform, and SQL.
2. **Task-Driven Context Compiler (<=4 Files Cap):** Progressive disclosure of task context strictly bounded by a 4-file cap and ~40-line character-offset snippets.
3. **Mathematical Blast Radius & Impact Analysis:** Computes calibrated multi-hop reachability across call graphs, inheritance chains, and database tables.
4. **Cross-Language Boundary Bridges:** HTTP boundary bridge (`fetch`/`axios` to backend route handlers via `:param` normalization), SQL def-use bridge (`READS` vs `WRITES`), subprocess bridge, and config key bridge.
5. **Universal Namespace Isolation:** Strict runtime prefixes (`py:`, `ts:`, `go:`, `rs:`, `java:`, etc.) preventing cross-language graph collision blowouts.
6. **9 Deterministic Materialized Lenses:** On-demand sub-projections for `Module`, `Symbol`, `Call`, `Class`, `Data`, `Entity`, `Config`, `Process`, and `Exception`.
7. **Git Temporal Intelligence:** 180-day exponential half-life decay mining uncovering hidden co-change matrices and `CO_CHANGED_WITH` edges.
8. **11-Tool Dual-Transport MCP Server:** Native JSON-RPC stdio and Streamable HTTP ASGI transports supporting 20+ AI assistant platforms (Antigravity IDE, Claude Code, Cursor, Codex, Gemini, Copilot, etc.).
9. **Quantifiable ROI & Telemetry Scoreboard:** Real-time tracking of token savings, avoided file reads, and dollar cost reduction relative to an unconstrained blast-radius baseline.
10. **Interactive Canvas Visualizer & Obsidian Vault Export:** Standalone local D3 force viewer (`graph.html`) and native Obsidian Markdown second-brain export.

---

## Quickstart

### Installation

```bash
# Global installation via pipx
pipx install git+https://github.com/pratiyush-DA/repopeekv2.git

# Or via uv
uv tool install git+https://github.com/pratiyush-DA/repopeekv2.git
```

### Basic Commands

```bash
# Index current repository
repopeek --repo-path .

# Compile focused context for a coding task (<=4 files)
repopeek --context "add customer discount tier to billing pipeline"

# Upstream blast radius analysis
repopeek --impact table.invoices

# Real-time token and cost savings ROI scoreboard
repopeek --savings

# Interactive local browser graph viewer
repopeek --view

# Launch stdio MCP server for AI coding agents
repopeek --serve-mcp
```

---

## Architecture Documentation Suite

Detailed architectural specifications are located in [Archietecture_Documentation/](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/):
- [01_EXECUTIVE_SUMMARY_AND_VISION.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/01_EXECUTIVE_SUMMARY_AND_VISION.md)
- [02_SYSTEM_ARCHITECTURE_AND_PIPELINE.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/02_SYSTEM_ARCHITECTURE_AND_PIPELINE.md)
- [03_PARSING_BRIDGES_AND_LENS_SPECIFICATION.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/03_PARSING_BRIDGES_AND_LENS_SPECIFICATION.md)
- [04_STORAGE_INDEXING_AND_GIT_INTELLIGENCE.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/04_STORAGE_INDEXING_AND_GIT_INTELLIGENCE.md)
- [05_STORY_CASCADE_AND_CONTEXT_COMPILER.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/05_STORY_CASCADE_AND_CONTEXT_COMPILER.md)
- [06_MCP_SERVER_CLI_AND_INTERFACES.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/06_MCP_SERVER_CLI_AND_INTERFACES.md)
- [07_IMPLEMENTATION_ROADMAP_AND_PHASING.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/07_IMPLEMENTATION_ROADMAP_AND_PHASING.md)
- [08_GRAPHIFY_HYBRID_INTEGRATION_BLUEPRINT.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/08_GRAPHIFY_HYBRID_INTEGRATION_BLUEPRINT.md)
- [09_TELEMETRY_SAVINGS_AND_ROI_SCOREBOARD.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/09_TELEMETRY_SAVINGS_AND_ROI_SCOREBOARD.md)
- [10_COMPREHENSIVE_PLATFORM_AND_ECOSYSTEM_SUPPORT.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/10_COMPREHENSIVE_PLATFORM_AND_ECOSYSTEM_SUPPORT.md)
- [11_CODING_ARCHITECTURE_AND_DESIGN_PATTERNS.md](file:///c:/Users/pkumar2/OneDrive%20-%20Data%20Axle/Documents/AI_INIT/RepopeekV2/Archietecture_Documentation/11_CODING_ARCHITECTURE_AND_DESIGN_PATTERNS.md)

---

## Notion Customer Portal

Customer setup guides, usage examples, and full feature specifications are published on Notion:
- [REPOPEEK_ARC:V2 on Notion](https://app.notion.com/p/REPOPEEK_ARC-V2-3f40f043dc1a81179f18d5ed02deec2e)
