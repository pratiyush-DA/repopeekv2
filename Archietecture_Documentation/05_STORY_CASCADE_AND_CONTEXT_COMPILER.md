# 05 - Story Cascade & Context Compiler

## 1. 5-Tier Story Cascade & Anti-Hallucination Guardrails

While deterministic AST graphs provide ground truth, natural-language coding agents require high-level summaries of code intent and design rationale. Naive LLM summarization often introduces hallucinations (invented parameters, hallucinated dependencies). 

RepoPeek implements a **5-Tier Story Cascade** with a strict, automated **Fact Verifier**:

```
+----------------------------------------------------------------------------------------------------+
| 5-TIER STORY CASCADE                                                                               |
|                                                                                                    |
|  [Tier 1: AST Fact Templates]       Deterministic zero-cost syntax cards from AST parser.          |
|              │                                                                                     |
|              ▼                                                                                     |
|  [Tier 2: SHA-256 Story Cache]      Disk-persisted cache keyed by symbol content hash.             |
|              │                                                                                     |
|              ▼ (Cache Miss)                                                                        |
|  [Tier 3: Cheap-Model Summaries]    Groq (qwen3.8-27b) or local model structured JSON extraction.  |
|              │                                                                                     |
|              ▼                                                                                     |
|  [Tier 4: Bottom-Up Aggregation]    Hierarchical rollups: Symbol -> Class -> File -> Community.    |
|              │                                                                                     |
|              ▼                                                                                     |
|  [Tier 5: AST Fact Verifier]        Validates claims against AST reality; falls back on fail.      |
+----------------------------------------------------------------------------------------------------+
```

### 1.1 Tier 1: Deterministic AST Fact Templates (Zero Cost)
Constructs a structured Markdown summary directly from the AST without any LLM inference:
- Name, signature, and parameter types.
- Docstrings and inline `# NOTE:`, `# WHY:`, `# HACK:` comments.
- Extracted static facts: calls made, variables/tables written, exceptions raised.

### 1.2 Tier 2: SHA-256 Story Cache
- Every symbol has a SHA-256 hash computed over its exact AST subtree text.
- If the hash matches an entry in `.repopeek/cache/stories/`, the cached summary is loaded in <1ms without calling an LLM.

### 1.3 Tier 3: Cheap-Model Structured Summaries
- For cache misses when an LLM key is configured (Groq API key or local Ollama), generates structured JSON summaries.
- Uses fast, cost-effective models (e.g. Groq `qwen/qwen3.8-27b`, with optional strong tier `openai/gpt-oss-120b`).
- Enforces strict JSON schema: `summary`, `responsibilities`, `side_effects`, `assumptions`.

### 1.4 Tier 4: Bottom-Up Hierarchical Aggregation
Summaries are synthesized strictly bottom-up:
1. Functions and Methods ->
2. Classes and Enums ->
3. Files and Modules ->
4. Architectural Communities.
This guarantees that high-level subsystem notes accurately reflect the constituent code rather than generic speculation.

### 1.5 Tier 5: AST Fact Verifier Guardrail
The Fact Verifier inspects every LLM-generated claim against the verified AST facts of that symbol:
```python
def verify_story_claims(story: dict, ast_facts: dict) -> bool:
    """Verifies that all entities mentioned in the story actually exist in the AST facts."""
    for call in story.get("claimed_calls", []):
        if call not in ast_facts["calls"]:
            return False  # Hallucinated call site
    for write in story.get("claimed_writes", []):
        if write not in ast_facts["writes"]:
            return False  # Hallucinated data mutation
    for raise_type in story.get("claimed_raises", []):
        if raise_type not in ast_facts["raises"]:
            return False  # Hallucinated exception
    return True
```
*Failure Fallback:* If a claim fails verification, the LLM story is rejected, a warning is logged, and RepoPeek falls back immediately to the deterministic Tier 1 AST template.

---

## 2. Context Compiler (`repopeek.context.compiler`)

The primary purpose of RepoPeek for autonomous coding agents is `compile_context` / `repopeek_context`. When an agent receives an engineering task (e.g., *"Update MAX_RETRIES handling in InvoiceParser and persist failed status to database"*), feeding it the entire repository or a 30-file graph dump burns tokens and induces errors.

The Context Compiler synthesizes a compact, task-focused package conforming to strict limits:
- **Maximum 4 Files Cap:** Never dumps an open-ended list of files.
- **~40-Line Spans:** Extracts the exact target function and its surrounding lines (~1–2k tokens total).
- **Explicit Exclusion List:** Tells the agent what files *not* to touch.
- **Fact & Constraint Checklist:** Lists database tables affected, callers that must not break, and temporal co-change warnings.

```
+----------------------------------------------------------------------------------------------------+
| CONTEXT PACKAGE STRUCTURE                                                                          |
|                                                                                                    |
| 1. TASK OBJECTIVE & RESOLVED TARGETS                                                               |
|    - Primary symbol: py:repopeek/parser.py::InvoiceParser.parse                                    |
|    - Direct downstream: sql:schema.sql::table.invoices                                             |
|                                                                                                    |
| 2. FOCUS CODE SPANS (Strictly <=4 files, ~40 lines each)                                           |
|    - File 1: repopeek/parser.py (Lines 80-125)                                                     |
|    - File 2: repopeek/db/writer.py (Lines 45-88)                                                   |
|    - File 3: src/types/invoice.ts (Lines 12-48)                                                    |
|                                                                                                    |
| 3. INVARIANTS & CONSTRAINTS                                                                        |
|    - Table 'invoices' has a foreign key to 'merchants' (do not delete or orphan).                  |
|    - Temporal coupling: modifying parser.py co-changes with tests/test_parser.py 92% of the time.  |
|                                                                                                    |
| 4. EXCLUSIONS                                                                                      |
|    - Do NOT edit repopeek/legacy/old_parser.py or schema migrations.                               |
+----------------------------------------------------------------------------------------------------+
```

### 2.1 3-Tier Progressive Disclosure

The Context Compiler supports three disclosure levels to match agent reasoning steps:

| Level | Name | Token Budget | Information Delivered |
|---|---|---|---|
| **Level 1** | *Orientation* | ~300 tokens | Candidate symbol names, file paths, and function signatures. |
| **Level 2** | *Actionable Pack* | ~1,500 tokens | Capped focus spans (≤4 files, ~40 lines), exact blast radius, affected tables. |
| **Level 3** | *Deep Plan & Risk* | ~3,000 tokens | Full call chains, temporal co-change files, test suites, step-by-step risk plan. |

---

## 3. Change Plan Engine (`repopeek.context.planner`)

Accessible via CLI (`--plan "<task>"`) or MCP tool (`repopeek_plan`), the Change Plan Engine generates a risk-assessed, step-by-step implementation plan before an agent begins modifying code.

### Plan Synthesis Algorithm
1. **Target Identification:** Parses the natural language task and resolves seed symbols using BM25 and AST symbol scoring.
2. **Blast Radius Computation:** Executes recursive SQLite CTE to identify all direct callers, data writes, and HTTP routes connected to seed symbols.
3. **Temporal Co-Change Lookup:** Queries `CO_CHANGED_WITH` edges to surface files that frequently require synchronized updates.
4. **Step Sequencing & Risk Scoring:**
   - Evaluates blast radius size and cyclomatic complexity.
   - Assigns Risk Level: `LOW`, `MEDIUM`, `HIGH`.
   - Organizes steps into: *Pre-flight verification*, *Implementation sequence*, and *Regression testing*.

### Sample Generated Plan Output

```markdown
# Change Plan: Raise MAX_LLM_RETRIES in metadata generation

- Risk Level: MEDIUM (3 callers affected, 1 SQL table write)
- Estimated Token Impact: 1,420 tokens

## Step 1: Update Configuration Constant
- Target: py:repopeek/config.py::MAX_LLM_RETRIES (Lines 15-22)
- Action: Increase default value from 3 to 5.

## Step 2: Modify Retry Loop in Metadata Generator
- Target: py:repopeek/meta/generator.py::MetadataGenerator.generate (Lines 88-124)
- Action: Pass new retry budget to retry decorator; handle ExpiredRetryException.

## Step 3: Verify Downstream Callers & Database Logging
- Affected Callers:
  - py:repopeek/orchestrator.py::Pipeline.run_stage
  - py:repopeek/cli.py::cmd_generate
- Data Entity: sql:table.generation_logs (WRITES)

## Step 4: Synchronized Co-Change Tests
- Temporal Co-Change: tests/test_meta_generator.py (P = 0.88)
- Run: pytest tests/test_meta_generator.py -k test_retry_exhaustion
```
