# 11 - Coding Architecture, Design Patterns & Engineering Standards

## 1. Governing Engineering Disciplines

RepoPeek's codebase is governed by three foundational engineering frameworks:

```
+----------------------------------------------------------------------------------------------------+
| REPOPEEK THREE-TIER ENGINEERING GOVERNANCE                                                         |
|                                                                                                    |
| 1. PONYTAIL (Extreme Simplicity & Anti-Hallucination)                                              |
|    - Stop at the first rung of the ladder: YAGNI -> Local Code -> Stdlib -> Dep -> 1 Line -> Min Code. |
|    - Root-cause fixes: fix the shared function where all callers route through, not symptoms.      |
|    - Anti-Hallucination Gate: Non-trivial logic MUST leave behind a runnable assert-based check.   |
|    - Mark deliberate shortcuts with `# ponytail: <ceiling> -> upgrade path <X>`.                   |
|                                                                                                    |
| 2. AGENT-SKILLS (Structured SDLC & Anti-Rationalization)                                           |
|    - Rigorous stage gating: Spec -> Plan -> Build -> Verify -> Review -> Ship.                     |
|    - Zero skipped steps: tests written before or alongside code, never deferred.                  |
|    - Thin incremental slices: changes delivered in testable atomic units touching <=4 files.      |
|                                                                                                    |
| 3. GRAPHIFY HERITAGE (Local-First Engine Robustness)                                               |
|    - Zero cloud leakage: 100% local AST extraction, no mandatory external LLM APIs.                |
|    - Fault-tolerant multi-worker extraction with recursion limit ceilings (_RECURSION_LIMIT=10,000)|
|    - 100% language parity across 40+ programming languages and 103+ file extensions.               |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Package Directory Layout (`repopeek/`)

The repository adopts a clean, modular Python package structure where every component has a single, cohesive responsibility:

```
repopeek/
├── __init__.py                 # Version, public symbols, export API
├── __main__.py                 # python -m repopeek CLI entrypoint dispatch
├── cli.py                      # Unified argparse CLI command interface
├── detect.py                   # Discovery, 103+ extensions, shebang dispatch, safety caps
├── extract.py                  # Polyglot extractor dispatcher, ProcessPoolExecutor, fallback
├── extractors/                 # Specialized language AST extractors (Tree-sitter & native)
│   ├── base.py                 # Shared extractor helpers, ID sanitization, byte/line offsets
│   ├── python.py               # Python stdlib ast + tree-sitter extractor, rationale extraction
│   ├── js_ts.py                # JS/TS/TSX/MTS/CTS/Vue/Svelte/Astro extractor
│   ├── go.py                   # Go structs, interfaces, methods, goroutines
│   ├── rust.py                 # Rust structs, traits, impls, Cargo workspace introspection
│   ├── jvm.py                  # Java, Kotlin, Scala, Groovy/Gradle extractors
│   ├── native.py               # C, C++, CUDA, Metal, Zig extractors (with header/impl merging)
│   ├── dotnet.py               # C#, VB.NET, Razor, XAML, Solution/Project extractors
│   ├── apple.py                # Swift, Objective-C, Objective-C++ extractors
│   ├── script.py               # Ruby, PHP, Blade, Lua, PowerShell, Bash, Robot, Terraform
│   ├── functional.py           # Elixir, Erlang, OCaml, Common Lisp, Dart
│   ├── scientific.py           # R, Julia, Fortran (with CPP preprocessor)
│   ├── legacy.py               # Pascal/Delphi/Lazarus, COBOL extractors
│   ├── domain.py               # Verilog, Solidity, Apex, BYOND DM extractors
│   └── sql.py                  # SQL DDL schemas and DML def-use flows
├── build.py                    # NetworkX DiGraph assembly, universal namespace isolation
├── cluster.py                  # Leiden community clustering (graspologic_native / Louvain)
├── lenses.py                   # 9 materialized sub-projections (Module..Exception)
├── bridges/                    # Cross-language boundary bridges
│   ├── http.py                 # HTTP client-to-route bridge (:param wildcard normalizer)
│   ├── sql.py                  # Application-to-table def-use bridge (READS/WRITES)
│   ├── process.py              # Subprocess to shell script execution bridge (EXECUTES)
│   └── config.py               # Env var / config key binding bridge (CONFIGURES)
├── storage.py                  # Dual storage: Content-addressed JSON shards + SQLite CTE cache
├── temporal.py                 # Git commit log mining, 180-day exponential half-life decay
├── context/                    # Task Context Compiler & Change Planner
│   ├── compiler.py             # Progressive disclosure compiler (<=4 files, ~40-line spans)
│   ├── planner.py              # 4-phase risk-assessed structured change plan engine
│   └── verifier.py             # AST Fact Verifier anti-hallucination guardrail
├── telemetry.py                # ROI scoreboard, counterfactual baseline, in-line scorecards
├── serve.py                    # 11-tool MCP server (stdio JSON-RPC + Streamable HTTP ASGI)
├── watch.py                    # Debounced sub-50ms incremental filesystem sync daemon
├── exporters/                  # Knowledge graph and visualizer exporters
│   ├── html.py                 # Standalone D3 force-directed viewer (graph.html)
│   ├── tree.py                 # Collapsible D3 tree view (GRAPH_TREE.html)
│   ├── callflow.py             # Interactive Mermaid call-flow HTML generator
│   └── obsidian.py             # Native Obsidian Markdown vault exporter
└── install.py                  # 20+ AI assistant platform installer and hook guards
```

---

## 3. Core Data Structures & Type Models

All core data transfer objects are strictly typed using standard library `dataclasses` with slot optimization for high throughput and zero unnecessary dependencies:

### 3.1 Node Record Model (`repopeek.models.NodeRecord`)
```python
@dataclass(slots=True)
class NodeRecord:
    id: str                         # Universal namespaced ID (e.g. "py:services/invoice.py::InvoiceParser.parse")
    kind: str                       # function, class, interface, method, table, config_key, route, file
    label: str                      # Human-readable display symbol name
    file_path: str                  # Relative path to source file
    start_line: int                 # 1-indexed starting line number
    end_line: int                   # 1-indexed ending line number
    start_byte: int                 # 0-indexed character/byte start offset for slicing
    end_byte: int                   # 0-indexed character/byte end offset
    docstring: str = ""             # Extracted docstring / header comments
    lenses: set[str] = field(default_factory=set) # Matched lens tags (Module, Symbol, Call, etc.)
    reads: list[str] = field(default_factory=list) # Variables or tables read
    writes: list[str] = field(default_factory=list) # Variables or tables mutated
    raises: list[str] = field(default_factory=list) # Exceptions thrown
    external: bool = False          # True if stub node representing 3rd-party library / built-in
```

### 3.2 Edge Record Model (`repopeek.models.EdgeRecord`)
```python
@dataclass(slots=True)
class EdgeRecord:
    source: str                     # Source namespaced node ID
    target: str                     # Target namespaced node ID
    relation: str                   # CALLS, INVOKES, INHERITS, IMPLEMENTS, READS, WRITES, etc.
    confidence: float = 1.0         # 1.0 for EXTRACTED AST facts, 0.75 for INFERRED bridges
    lenses: set[str] = field(default_factory=set) # Matched lens tags
    evidence: str = ""              # Code snippet, line number, or commit hash evidencing edge
```

### 3.3 Context Package Model (`repopeek.models.ContextPackage`)
```python
@dataclass(slots=True)
class ContextSnippet:
    file_path: str
    symbol_id: str
    start_line: int
    end_line: int
    code_text: str

@dataclass(slots=True)
class ContextPackage:
    task: str                       # User prompt / task intent
    level: int                      # Progressive disclosure level (1=Summary, 2=Pack, 3=Deep)
    file_count: int                 # Guaranteed <= 4 files
    snippets: list[ContextSnippet]  # Sliced ~40-line code units
    invariants: list[str]           # Parameter types, return shapes, exception constraints
    affected_tests: list[str]       # Associated test symbols
    estimated_tokens: int           # Token budget estimate (~1-2k tokens)
    scorecard: dict[str, Any]       # Counterfactual baseline vs compiled savings
```

---

## 4. Software Design Patterns

RepoPeek deliberately applies classical, battle-tested software design patterns:

### 4.1 Adapter Pattern (Wrapping Graphify Extractor Dispatch)
Instead of modifying Graphify's core extractors or rewriting them, RepoPeek uses the Adapter pattern to wrap `_safe_extract`:
```python
class PolyglotExtractorAdapter:
    """Adapts upstream Graphify extractors, injecting namespace prefixes and exact byte spans."""
    def __init__(self, upstream_dispatch: dict[str, Callable]):
        self._dispatch = upstream_dispatch

    def extract_file(self, file_path: Path) -> ExtractionResult:
        ext = file_path.suffix.lower()
        extractor = self._dispatch.get(ext) or self._resolve_shebang(file_path)
        if not extractor:
            return ExtractionResult.empty()
        
        raw_result = _safe_extract(extractor, file_path)
        return self._normalize_ast_facts(file_path, raw_result)
```

### 4.2 Strategy Pattern (Materialized Lens Projections)
Rather than writing 9 different graph traversal engines, RepoPeek applies the Strategy pattern over a single unified NetworkX property graph:
```python
class LensProjectionStrategy:
    def __init__(self, lens_name: str):
        self.lens_name = lens_name

    def filter(self, graph: nx.DiGraph) -> nx.DiGraph:
        valid_nodes = [n for n, d in graph.nodes(data=True) if self.lens_name in d.get("lenses", set())]
        sub = graph.subgraph(valid_nodes).copy()
        invalid_edges = [(u, v) for u, v, d in sub.edges(data=True) if self.lens_name not in d.get("lenses", set())]
        sub.remove_edges_from(invalid_edges)
        return sub
```

### 4.3 Repository Pattern (Dual Storage Engine)
The dual storage engine abstracts persistence behind a clean Repository interface:
- **Write:** Persists content-addressed JSON shards under `.repopeek/shards/` and synchronizes SQLite tables in `cache.db`.
- **Read:** Executes sub-millisecond recursive Common Table Expressions (CTEs) in SQLite for graph traversals and reachability queries.

---

## 5. Testing & Verification Standards (Agent-Skills + Ponytail)

1. **Red-Green-Refactor Loop:** Every feature or bug fix starts with an executable test reproducing expected behavior before production code is committed.
2. **Anti-Hallucination Runnable Self-Checks:** Every non-trivial module in `repopeek/` includes a lightweight, self-contained `if __name__ == "__main__":` verification block or an explicit test in `tests/`.
3. **Strict Coverage on Golden Scenarios:**
   - Multi-Language Blast Radius (Python -> SQL -> Shell -> YAML).
   - Data Flow Traceability (`READS` vs `WRITES` separation).
   - Context Compiler Token Budget (strictly `<=4 files`, `~40 lines`, `~1–2k tokens`).
4. **Git Commit Constraint:** Every completed task or feature MUST be cleanly committed and pushed to `origin main` on `https://github.com/pratiyush-DA/repopeekv2.git`.
