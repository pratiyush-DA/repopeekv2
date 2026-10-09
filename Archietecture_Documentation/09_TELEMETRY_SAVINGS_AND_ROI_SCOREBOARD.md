# 09 - Telemetry, Savings & ROI Scoreboard Engine

## 1. Overview & Motivation

When an autonomous AI coding agent uses RepoPeek to implement a task, it navigates via focused context packs (≤4 files, ~40-line spans, ~1–2k tokens) instead of reading dozens of whole files across the repository.

To provide users and engineering teams with transparent, quantifiable visibility into context efficiency, RepoPeek includes an integrated **Telemetry, Savings & ROI Scoreboard Engine** (`repopeek.telemetry.savings`).

Every task execution automatically measures:
1. **Tokens Saved:** Difference between the counterfactual full-file blast radius and the compiled ~40-line snippet pack.
2. **Files Avoided:** Total count of full files the agent did not have to read or grep.
3. **Estimated Dollar Savings:** Projected LLM API cost reduction based on standard model token pricing.
4. **Context Saturation Index:** Percentage reduction in agent context window consumption.

---

## 2. Mathematical Formulation & Counterfactual Model

```
+----------------------------------------------------------------------------------------------------+
| TELEMETRY FORMULATION                                                                              |
|                                                                                                    |
|  Counterfactual Baseline (Without RepoPeek):                                                       |
|  - Agent explores the blast radius by fetching full files across upstream callers,                 |
|    downstream dependencies, and touched database tables.                                           |
|  - S_files_baseline = Total set of files in transitive blast radius (or target search directory). |
|  - T_baseline = Sum of tokens across all S_files_baseline.                                          |
|                                                                                                    |
|  RepoPeek Delivery (With RepoPeek):                                                                |
|  - Context Compiler extracts focused spans strictly capped at <=4 files with ~40 lines each.       |
|  - S_files_delivered = Pack files (len <= 4).                                                      |
|  - T_delivered = Actual tokens in compiled context pack (~1,000 - 2,000 tokens).                   |
|                                                                                                    |
|  Delta & Efficiency Metrics:                                                                       |
|  - Tokens Saved:         Delta_tokens = T_baseline - T_delivered                                   |
|  - Token Reduction %:    R_token = (Delta_tokens / T_baseline) * 100                               |
|  - Files Avoided:        Delta_files = len(S_files_baseline) - len(S_files_delivered)              |
|  - Cost Saved ($):       Savings_USD = (Delta_tokens / 1,000,000) * P_model                        |
|    (where P_model = configurable rate, default $3.00 / 1M input tokens e.g. Sonnet 3.5 / GPT-4o)   |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Storage & Telemetry Ledger

All savings events are appended atomically to a local JSONL ledger and mirrored in the SQLite cache:

- **Ledger Path:** `.repopeek/telemetry/savings.jsonl`
- **SQLite Table:**
```sql
CREATE TABLE IF NOT EXISTS telemetry_savings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    task_description TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    baseline_files_count INTEGER NOT NULL,
    delivered_files_count INTEGER NOT NULL,
    baseline_tokens INTEGER NOT NULL,
    delivered_tokens INTEGER NOT NULL,
    tokens_saved INTEGER NOT NULL,
    token_reduction_pct REAL NOT NULL,
    cost_saved_usd REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_telemetry_session ON telemetry_savings(session_id);
```

### Event Payload Schema
```json
{
  "event_id": "evt_98f4a12",
  "session_id": "sess_20261009_1520",
  "task": "Update MAX_RETRIES handling in InvoiceParser and persist failed status",
  "timestamp": "2026-10-09T17:21:00Z",
  "baseline": {
    "files_count": 18,
    "files": ["repopeek/parser.py", "repopeek/db/writer.py", "src/types/invoice.ts", "..."],
    "total_tokens": 54200
  },
  "delivered": {
    "files_count": 3,
    "files": ["repopeek/parser.py", "repopeek/db/writer.py", "src/types/invoice.ts"],
    "total_tokens": 1420
  },
  "savings": {
    "files_avoided": 15,
    "tokens_saved": 52780,
    "reduction_pct": 97.38,
    "estimated_cost_saved_usd": 0.158
  }
}
```

---

## 4. Presentable Surfaces

RepoPeek surfaces efficiency metrics across **5 distinct presentation interfaces**:

### 4.1 In-Line Context Package Scorecard (MCP Tool Payload)
Every time `repopeek_context` or `repopeek_context_pack` executes, it prepends an ASCII efficiency card to the context package returned to the agent:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ REPOPEEK EFFICIENCY SCORECARD                                          │
│ Task: Update MAX_RETRIES handling in InvoiceParser                     │
├────────────────────────────────────────────────────────────────────────┤
│ Context Delivered:   3 files | 124 lines | 1,420 tokens                │
│ Baseline Avoided:   18 files | 4,810 lines | 54,200 tokens             │
│ Tokens Saved:       52,780 tokens (97.4% reduction)                    │
│ Full Files Avoided: 15 full files kept out of agent context            │
│ Est. Cost Saved:    $0.16 (based on $3.00/1M tokens)                   │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Dedicated MCP Tool: `repopeek_savings`
An 11th tool exposed over stdio MCP allowing agents or users to query cumulative or session-specific savings at any time:

- **Tool Name:** `repopeek_savings`
- **Parameters:**
  - `timeframe`: `"current_session"` (default), `"today"`, or `"all_time"`.
- **Return Output:** Formatted Markdown scoreboard summarizing total tasks completed, cumulative tokens saved, files avoided, and net cost reduction.

### 4.3 CLI Scorecard Command
Users running in terminal can inspect their metrics instantly:

```bash
python -m repopeek.cli --savings
```

**Terminal Output:**
```text
================================================================================
                      REPOPEEK CONTEXT EFFICIENCY HUD
================================================================================
  Timeframe:                     Last 24 Hours (7 agent tasks)
  Total Context Delivered:       10,240 tokens
  Full Baseline Equivalent:      384,100 tokens
--------------------------------------------------------------------------------
  TOTAL TOKENS SAVED:            373,860 tokens (97.3% reduction)
  FULL FILES AVOIDED:            96 files
  ESTIMATED COST SAVED:          $1.12 USD
  AVERAGE CONTEXT PACK SIZE:     1,462 tokens / task
================================================================================
```

### 4.4 Interactive Web Viewer HUD Widget (`graph.html`)
The standalone D3 web viewer includes a collapsible **Efficiency & Savings HUD** in the top navigation bar:
- Displays a live token counter.
- Dynamic meter showing context reduction percentage.
- Expandable drawer breaking down savings by community and recent tasks.

### 4.5 Obsidian Second Brain Integration
Cumulative savings are autonomously recorded into the daily session note in the user's Obsidian vault (`03_Sesiones/YYYY-MM-DD - RepopeekV2.md`) and summarized in `00_RepoPeek_Index.md`.
