# 10 - Comprehensive Platform, Polyglot & Ecosystem Support

## 1. Executive Mandate

RepoPeek inherits and maintains 100% parity with Graphify's broad ecosystem support. Rather than limiting the engine to a single IDE or a subset of languages, RepoPeek natively supports:

1. **20+ AI Assistant Platforms** with automated skill installation, configuration rules, and `PreToolUse` hook guards.
2. **40+ Programming Language Grammars & File Types** (code, package manifests, docs, PDFs, Office, audio/video).
3. **Multi-Format Visual & Knowledge Exporters** (D3 Force Graph, Collapsible Tree, Callflow Mermaid, Obsidian Vault, Markdown Wiki, SVG, GraphML, Neo4j, FalkorDB).
4. **Dual MCP Server Transports** (Local Stdio JSON-RPC + Streamable HTTP ASGI with API key authentication).
5. **Multi-Provider LLM Backends** (Claude/Anthropic, Gemini, OpenAI, Ollama, Azure OpenAI, AWS Bedrock, DeepSeek, Moonshot/Kimi).
6. **Git Lifecycle Hooks & GitHub PR Review Suite** (`hook install`, merge drivers, strict-mode read interception, PR blast radius triage).

```
+----------------------------------------------------------------------------------------------------+
| REPOPEEK FULL ECOSYSTEM SUPPORT MATRIX                                                             |
|                                                                                                    |
| 20+ AI Platforms:     Claude Code, Cursor, Codex, OpenCode, Kilo, Copilot, Aider, OpenClaw,        |
|                       Factory Droid, Trae, Gemini CLI, Hermes, Kimi, Amp, Kiro, Pi, Devin,          |
|                       Google Antigravity, VS Code Copilot Chat, Agent Skills spec.                 |
|                                                                                                    |
| 40+ Grammars & Media: Python, TS/JS, Go, Rust, Java, C/C++, C#, Kotlin, Swift, Ruby, PHP,         |
|                       Scala, Lua, Zig, PowerShell, Elixir, Erlang, Dart, R, Julia, OCaml,          |
|                       Common Lisp, Fortran, Pascal, COBOL, Apex, Solidity, Verilog, SQL,           |
|                       Shell, Robot, Terraform, PDFs, Office (.docx/.xlsx), G-Workspace, Audio/Video|
|                                                                                                    |
| Multi-Exporters:      Interactive D3 graph.html, Collapsible Tree HTML, Callflow Mermaid HTML,     |
|                       Native Obsidian Vault, Markdown Wiki, SVG, GraphML, Neo4j, FalkorDB.         |
|                                                                                                    |
| Dual Transports:      Stdio JSON-RPC + Streamable HTTP ASGI (Starlette, SSE, API Key Gate).        |
|                                                                                                    |
| PR & Git Lifecycle:   Pre-commit/checkout hooks, strict read interception, PR blast triage.        |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. 20+ AI Assistant Platforms Support Matrix

RepoPeek implements Graphify's automated platform installer (`repopeek install --platform <name>`) and persistent configuration hooks:

| Platform | Integration Mechanism | Installed Configuration & Rule Files |
|---|---|---|
| **Google Antigravity** | Native Skill & Hooks | `~/.gemini/config/skills/repopeek/` or `.agents/skills/repopeek/` + `AGENTS.md` |
| **Hermes Core** | Native Skill & Brain Sync | `.agents/skills/repopeek/SKILL.md` + direct Obsidian session hook |
| **Claude Code (Mac/Linux/Win)** | PreToolUse Hooks & Skill | `~/.claude/skills/repopeek/` + `.claude/settings.json` (hook-guard interception) |
| **Cursor** | Native MDC Rules | `.cursor/rules/repopeek.mdc` (`alwaysApply: true` auto-inclusion) |
| **Codex** | Instruction Files & Skill | `~/.codex/skills/repopeek/` + `AGENTS.md` (`hook-check` no-op compatibility) |
| **OpenCode** | Skill & Instruction Hook | `~/.config/opencode/skills/repopeek/` + `AGENTS.md` |
| **Kilo Code** | Skill, Command & Plugin | `~/.config/kilo/skills/` + `/repopeek` command + `.kilo/plugins/repopeek.js` |
| **GitHub Copilot CLI** | Skill / Configuration | `~/.copilot/skills/repopeek/` + environment hook |
| **VS Code Copilot Chat** | VS Code workspace rules | `.vscode/settings.json` + `AGENTS.md` |
| **Aider** | Persistent Conventions | `.aider.conf.yml` conventions pointing to RepoPeek graph queries |
| **OpenClaw** | Agent Workspace Skill | `.openclaw/skills/repopeek/` |
| **Factory Droid** | Task Tool Dispatch | `~/.factory/skills/repopeek/` (supports parallel subagent exploration) |
| **Trae & Trae CN** | Agent Tool & AGENTS.md | `AGENTS.md` always-on graph navigation instruction block |
| **Gemini CLI** | PreToolUse Hook & Skill | `~/.gemini/skills/repopeek/` + `settings.json` pre-tool hook |
| **Kimi Code** | Native Assistant Skill | `~/.kimi/skills/repopeek/` |
| **Amp** | Native Tool Manifest | `.amp/skills/repopeek/` |
| **Agent Skills (Cross-Framework)**| Specification Target | `~/.agents/skills/repopeek/` (global) or `./.agents/skills/` (project-scoped) |
| **Kiro IDE / CLI** | Kiro Skill Integration | `~/.kiro/skills/repopeek/` |
| **Pi Coding Agent** | Assistant Module | `~/.pi/skills/repopeek/` |
| **Devin CLI** | Custom Tool Definition | `.devin/tools/repopeek.json` |

### PreToolUse Hook Interception & Strict Mode
RepoPeek carries Graphify's hook-guard architecture:
- **Soft Nudge Mode (Default):** Before an agent executes a raw search or reads files one-by-one, the hook injects an `additionalContext` reminder advising the agent to query `repopeek_context` or `repopeek_lookup`.
- **Strict Mode (`--strict`):** In Claude Code and compatible environments, RepoPeek denies the first raw source read of a session (`permissionDecision: "deny"`), redirecting the agent to query the graph first, and then automatically downgrades to soft mode so normal edits are never blocked.

---

## 3. Polyglot Matrix: 40+ Languages & Media Types

RepoPeek handles the full spectrum of file types extracted by Graphify:

### 3.1 Code & Configuration (AST via Tree-sitter & Specialized Parsers)
- **Web & Fullstack:** Python (`.py`), TypeScript (`.ts`, `.tsx`, `.mts`, `.cts`), JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`), Vue (`.vue`), Svelte (`.svelte`), Astro (`.astro`).
- **Systems & Native:** Rust (`.rs`), Go (`.go`), C (`.c`, `.h`), C++ (`.cpp`, `.cc`, `.cxx`, `.hpp`), CUDA (`.cu`, `.cuh`), Metal (`.metal`), Zig (`.zig`).
- **Enterprise & JVM:** Java (`.java`), Kotlin (`.kt`, `.kts`), Scala (`.scala`), Groovy/Gradle (`.groovy`, `.gradle`), C# (`.cs`, `.csproj`, `.sln`), VB.NET (`.vb`, `.vbproj`), F# (`.fsproj`), XAML (`.xaml`), ASP.NET (`.razor`, `.cshtml`).
- **Scripting & Dynamic:** Ruby (`.rb`), PHP (`.php`), Swift (`.swift`), Lua/Luau (`.lua`, `.luau`), PowerShell (`.ps1`, `.psm1`, `.psd1`), Bash/Shell (`.sh`, `.bash`), Dart (`.dart`), Elixir (`.ex`, `.exs`), Erlang (`.erl`, `.hrl`), R (`.r`), Julia (`.jl`).
- **Functional, Hardware & Scientific:** OCaml (`.ml`, `.mli`), Common Lisp (`.lisp`, `.cl`, `.asd`), Fortran (`.f`, `.f90`, `.f08`), Pascal/Delphi (`.pas`, `.dpr`, `.dfm`), COBOL (`.cbl`, `.cob`), Verilog (`.v`, `.sv`, `.svh`).
- **Domain-Specific:** Salesforce Apex (`.cls`, `.trigger`), Solidity (`.sol`), BYOND DreamMaker (`.dm`, `.dme`), Robot Framework (`.robot`, `.resource`), Terraform / HCL (`.tf`, `.tfvars`, `.hcl`).
- **Data & Queries:** SQL (`.sql`, SQLGlot multi-dialect), JSON (`.json`), YAML (`.yaml`, `.yml`).

### 3.2 Manifests & Infrastructure Configurations
- MCP Configs: `.mcp.json`, `mcp.json`, `claude_desktop_config.json`.
- Package Manifests: `pyproject.toml`, `package.json`, `go.mod`, `pom.xml`, `Cargo.toml`.
- Synthesizes canonical dependency hubs connected via `DEPENDS_ON` edges.

### 3.3 Documents, Office & Multimodal Media
- Structured Docs: Markdown (`.md`, `.mdx`), Quarto (`.qmd`), HTML, RST, TXT with inter-document link resolution.
- Office Documents: Word (`.docx`) and Excel (`.xlsx`).
- Google Workspace: Native `.gdoc`, `.gsheet`, `.gslides` integration via `gws` CLI.
- PDFs: Extracted via PyPDF with section slicing.
- Visual Media: Image metadata (`.png`, `.jpg`, `.webp`, `.gif`).
- Audio & Video: Video/audio transcription powered by `faster-whisper` and `yt-dlp` (supports local `.mp4`, `.mp3`, `.wav`, and YouTube URLs).

---

## 4. Multi-Format Exporters & Visualizers

RepoPeek generates all visualization and knowledge graph artifacts provided by Graphify:

| Output Artifact | Command / Trigger | Format & Interactivity |
|---|---|---|
| **Interactive Graph HTML** | `repopeek.cli --view` or `export.to_html()` | Standalone D3.js v7 force-directed viewer (`graph.html`). Features community clustering, 9-lens filter tabs, glow links, search, and blast-radius tracing. Zero external CDN dependencies. |
| **Collapsible Tree HTML** | `repopeek.cli tree` | Collapsible D3 tree view (`GRAPH_TREE.html`) with expandable directory/module hierarchies, depth palettes, and inspector drawers. |
| **Mermaid Callflow HTML** | `repopeek.cli export callflow-html` | Interactive call-flow visualization rendering sequence and flow diagrams via Mermaid.js. Auto-regenerates on git commit. |
| **Native Obsidian Vault** | `repopeek.cli --export-obsidian <dir>` | Complete Obsidian Markdown vault with YAML frontmatter, bidirectional `[[wikilinks]]`, `.obsidian/graph.json` color groupings, and `_COMMUNITY_*.md` overview notes. |
| **Markdown Wiki** | `repopeek.cli --wiki` | Hierarchical documentation wiki (`wiki/`) with one structured article per community and a master `index.md`. |
| **Vector SVG Graph** | `repopeek.cli export svg` | High-resolution publication-ready vector diagram (`graph.svg`) rendered via Matplotlib. |
| **GraphML** | `export.to_graphml()` | Standard XML GraphML export compatible with Gephi, Cytoscape, and yEd. |
| **Neo4j Cypher** | `export.to_cypher()` or `--neo4j` | Cypher script or direct push to live Neo4j database instances. |
| **FalkorDB** | `--falkordb` | Direct graph push to low-latency FalkorDB instances. |

---

## 5. Dual MCP Transports: Local Stdio & Streamable HTTP

RepoPeek supports both deployment topologies supported by Graphify:

### 5.1 Local Stdio Transport (Per-Developer)
- Transport: JSON-RPC 2.0 over standard input and output (`stdio`).
- Used by: Antigravity IDE, Cursor, Claude Code, Claude Desktop, Codex.
- Features: Zero port conflicts, strict subprocess sandboxing, instant termination with client.

### 5.2 Streamable HTTP ASGI Transport (Shared / Team Server)
- Transport: Starlette ASGI application with Server-Sent Events (SSE) streaming and JSON-RPC.
- Launch Command: `python -m repopeek.cli --serve-http --host 0.0.0.0 --port 8080`
- Security & Middleware:
  - Constant-time API Key Gate (`X-API-Key` or `Authorization: Bearer <token>`).
  - Thread-safe multi-project context cache with LRU eviction (`GRAPHIFY_MAX_CONTEXTS`).
  - Session timeout management reaping idle stateful sessions.

---

## 6. Git Lifecycle & GitHub PR Review Suite

RepoPeek incorporates Graphify's complete workflow automation suite:

### 6.1 Git Hook Automation (`repopeek hook install`)
- Post-Commit Hook: Rebuilds code AST incrementally in background on every commit (zero API cost).
- Post-Checkout / Post-Switch Hook: Detects branch changes and updates graph topology automatically.
- Custom Git Merge Driver: Automatically resolves merge conflicts on `graph.json` during branch merges.

### 6.2 GitHub PR Review & Blast Radius Triage (`repopeek prs`)
- `repopeek prs`: PR dashboard showing open pull requests, CI status, review approvals, and worktree mapping.
- `repopeek prs <number>`: Computes exact graph impact for a specific PR (touched communities, affected nodes, caller risk).
- `repopeek prs --triage`: Ranks actionable pull requests by merge risk (higher blast radius = higher merge risk).
- `repopeek prs --conflicts`: Detects pull requests sharing graph communities, identifying merge-order conflict risks before CI fails.

---

## 7. Multi-Provider LLM Backends

For optional semantic passes over documents, PDFs, and high-level summaries, RepoPeek supports all Graphify backends:

| Backend Provider | Environment Variable / Flag | Primary Use Case |
|---|---|---|
| **Anthropic Claude** | `ANTHROPIC_API_KEY` (`--backend claude`) | High-reasoning architectural summaries and rationale extraction |
| **Google Gemini** | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Ultra-fast semantic pass with large multimodal document context |
| **OpenAI / OpenAI-Compatible** | `OPENAI_API_KEY` (`--backend openai`) | Default API integration, compatible with DeepSeek, vLLM, and LiteLLM |
| **Local Ollama** | `--backend ollama` (`OLLAMA_HOST`) | Fully private, offline semantic extraction (e.g. `llama3`, `qwen2.5`) |
| **Azure OpenAI** | `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT` | Enterprise compliant, private cloud deployment |
| **AWS Bedrock** | AWS IAM Credentials (`--backend bedrock`) | Native AWS cloud infrastructure integration |
| **Moonshot / Kimi** | `MOONSHOT_API_KEY` (`--backend kimi`) | Long-context Chinese and multilingual documents |
