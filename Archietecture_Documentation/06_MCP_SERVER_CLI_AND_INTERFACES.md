# 06 - MCP Server, CLI & Visualizers

## 1. Stdio JSON-RPC MCP Server (`repopeek.serve`)

RepoPeek implements a Model Context Protocol (MCP) server over standard input/output (`stdio`), exposing code intelligence directly to AI coding agents (Antigravity IDE, Cursor, Claude Code, Claude Desktop, and Codex).

### 1.1 MCP Configuration

Add the server definition to `mcp_config.json` or `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "repopeek": {
      "command": "python",
      "args": [
        "-m",
        "repopeek.cli",
        "--repo-path",
        "/absolute/path/to/target-repo",
        "--serve-mcp"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 1.2 The 10 Specialized Agent Tools

| Tool Name | Parameters | Return Value | Description & Agent Use Case |
|---|---|---|---|
| `repopeek_lookup` | `query` (str) | Formatted Markdown card | Looks up a symbol or entity by name or ID. Returns file location, line range, parameters, return type, and docstrings. |
| `repopeek_neighbors` | `query` (str), `relation_filter` (str?) | Neighbor list with edge types | Inspects immediate 1-hop inbound and outbound edges. Reveals direct callers, callees, imports, and mutations. |
| `repopeek_impact` | `target` (str), `max_depth` (int=3), `direction` (str="both") | Tree view of affected nodes | Calculates blast radius ("If I edit X, what breaks?"). Returns affected files, callers, and database tables. |
| `repopeek_data_trace` | `query` (str) | Data flow breakdown | Traces state def-use. Answers "Who writes entity X?" and "Who reads entity X?" across SQL and application code. |
| `repopeek_context_pack` | `targets` (list[str]), `token_budget` (int=2000) | Markdown context pack | Generates a budget-governed pack for known symbol IDs with zero fluff and exact line spans. |
| `repopeek_context` | `task` (str), `budget` (int=2000), `level` (int=2) | Context package (≤4 files) | Compiles natural-language task into focused **≤4 files with ~40-line snippets**, exclusions, and constraints. |
| `repopeek_plan` | `task` (str) | Risk-assessed change plan | Formulates a step-by-step engineering plan with risk levels, affected callers, and test verification recommendations. |
| `repopeek_routes` | *(none)* | Table of HTTP routes | Lists detected cross-language HTTP routes, matching client API calls (fetch/axios) to backend route handlers. |
| `repopeek_co_changes` | `target` (str) | Ranked list of coupled files | Surfaces files that temporally change together in git history (P ≥ 0.35) despite lacking direct static import links. |
| `repopeek_resolve` | `task` (str) | Ranked candidate symbols | Disambiguates and ranks symbol candidates matching a natural-language description using BM25 and graph centrality. |
| `repopeek_savings` | `timeframe` (str="current_session") | Markdown efficiency scorecard | Calculates and presents quantifiable token, file-fetching, and cost savings achieved compared to counterfactual raw-repo exploration. |

---

## 2. Command Line Interface (CLI)

The RepoPeek CLI provides comprehensive indexing and exploration commands:

### 2.1 Indexing & Serving
```bash
# Deterministic offline indexing (Zero LLM, local AST only)
python -m repopeek --repo-path /path/to/repo --output-dir ./output --offline

# Index with incremental watch daemon (<50ms sync on changes)
python -m repopeek --repo-path /path/to/repo --output-dir ./output --watch

# Start stdio MCP server for AI assistants
python -m repopeek.cli --repo-path /path/to/repo --serve-mcp
```

### 2.2 Instant Graph Queries
```bash
# Look up atomic symbol card
python -m repopeek.cli --lookup InvoiceParser.parse

# Compute blast radius tree
python -m repopeek.cli --impact InvoiceParser.parse --depth 4

# Trace data def-use for SQL table or variable
python -m repopeek.cli --trace table.invoices

# Compile task context pack (<=4 files, ~40-line spans)
python -m repopeek --context "Raise MAX_LLM_RETRIES in metadata generation" --output-dir ./output

# Generate step-by-step change plan
python -m repopeek.cli --plan "Add status column to users table and update auth check"

# Inspect cross-language HTTP boundary routes
python -m repopeek.cli --routes

# Inspect git temporal co-changes
python -m repopeek.cli --co-changes repopeek/parsers/python.py

# Display quantifiable tokens and file-fetching savings scoreboard
python -m repopeek.cli --savings
```

---

## 3. Interactive Web Graph Viewer (Obsidian-Style)

Launch a local, zero-dependency force-directed code property graph viewer in your browser:

```bash
python -m repopeek.cli --view
# Custom port:
python -m repopeek.cli --view --port 9000
```

```
+----------------------------------------------------------------------------------------------------+
| REPOPEEK WEB VIEWER CAPABILITIES                                                                   |
|                                                                                                    |
| 1. 9 Switchable Lenses:                                                                            |
|    Instant toolbar toggle between Call Graph, Module Hierarchy, Data Flow, Config, Exception, etc. |
|                                                                                                    |
| 2. Obsidian-Style Force Simulation:                                                                |
|    Smooth D3 v7 physics with community color clustering and dynamic link distance.                |
|                                                                                                    |
| 3. Interactive Blast-Radius Visualizer:                                                            |
|    Click any node -> triggers real-time glowing paths highlighting all transitive upstream callers  |
|    and downstream data mutations.                                                                  |
|                                                                                                    |
| 4. Symbol Inspector Drawer:                                                                        |
|    Slide-out drawer displaying file path, line numbers, docstrings, callers, and callees.          |
|                                                                                                    |
| 5. Zero External CDN Dependencies:                                                                 |
|    The HTML file is completely standalone with inlined D3 scripts and embedded graph JSON data.   |
+----------------------------------------------------------------------------------------------------+
```

---

## 4. Native Obsidian Vault Exporter (`--export-obsidian`)

RepoPeek exports the complete SCPG into a structured Obsidian Markdown vault:

```bash
python -m repopeek.cli --export-obsidian ./my_obsidian_vault
```

### Vault Structure
```
my_obsidian_vault/
├── .obsidian/
│   ├── graph.json                 # Pre-configured color groups for the 9 lenses
│   └── app.json                   # Obsidian display settings
├── 00_Overview/
│   ├── 00_RepoPeek_Index.md       # Master index with community statistics
│   └── _COMMUNITY_Core_Parser.md  # Community overview notes with Dataview queries
├── Symbols/
│   ├── InvoiceParser.parse.md     # Node notes with YAML frontmatter & [[wikilinks]]
│   └── table.invoices.md
└── Modules/
    └── repopeek.parsers.python.md
```

### Generated Note Frontmatter & Wikilink Structure
```markdown
---
id: "py:repopeek.parsers.python::PythonParser.parse"
label: "PythonParser.parse"
entity_type: "method"
runtime: "py"
source_file: "repopeek/parsers/python.py"
span: "L42-L95"
community: 3
lenses:
  - Symbol
  - Call
  - Class
---

# PythonParser.parse

> **Source:** `repopeek/parsers/python.py` (Lines 42–95)  
> **Community:** [[_COMMUNITY_AST_Parsers|AST Parsers]]

## Outgoing Relationships
- [[CALLS]] -> [[py:repopeek.parsers.base::BaseParser._validate_input|BaseParser._validate_input]]
- [[READS]] -> [[cfg:repopeek.config::PARSER_TIMEOUT|PARSER_TIMEOUT]]

## Incoming Relationships
- [[CALLS]] <- [[py:repopeek.orchestrator::Pipeline.run|Pipeline.run]]
- [[CO_CHANGED_WITH]] <-> [[repopeek/tests/test_python_parser.py]] (P = 0.91)
```
Opening this vault in **Obsidian Desktop** allows developers and agents to explore the codebase using Obsidian's native **Graph View** with full-text search and visual community clustering.
