# 03 - Polyglot Parsing (40+ Languages), Bridges & 9 Lenses Specification

## 1. Comprehensive Polyglot Parsing Substrate (100% Graphify Parity)

RepoPeek delivers zero-leakage, local static analysis that parses the complete spectrum of programming languages supported by Graphify: **40+ programming and markup languages** and **103+ file extensions**.

```
+----------------------------------------------------------------------------------------------------+
| REPOPEEK POLYGLOT PARSER DISPATCH ARCHITECTURE                                                     |
|                                                                                                    |
|  [Source Files (103+ Extensions)]                                                                 |
|         │                                                                                          |
|         ├── Ext Match (_DISPATCH) / Shebang Match (_SHEBANG_DISPATCH)                              |
|         ▼                                                                                          |
|  +-----------------------------------------------------------------------------------------------+ |
|  | PARSER TIERS (Tree-sitter Grammars + Native Specialized Extractors)                           | |
|  | - Tier 1: Web & Dynamic Fullstack (Python, TS, JS, TSX, JSX, Vue, Svelte, Astro)               | |
|  | - Tier 2: Systems & Native (Rust, Go, C, C++, CUDA, Metal, Zig)                               | |
|  | - Tier 3: Enterprise & JVM (Java, Kotlin, Scala, Groovy, Gradle, C#, VB.NET, Razor, XAML)     | |
|  | - Tier 4: Apple Ecosystem (Swift, Objective-C, Objective-C++)                                 | |
|  | - Tier 5: Scripting & Automation (Ruby, PHP, Blade, Lua, PowerShell, Bash, Robot, Terraform)   | |
|  | - Tier 6: Concurrent & Functional (Elixir, Erlang, OCaml, Common Lisp, Dart)                  | |
|  | - Tier 7: Scientific & Numeric (R, Julia, Fortran)                                            | |
|  | - Tier 8: Legacy & Enterprise (Pascal/Delphi/Lazarus, COBOL)                                  | |
|  | - Tier 9: Hardware, Blockchain & Domain (Verilog/SystemVerilog, Solidity, Apex, BYOND DM, SQL)| |
|  +-----------------------------------------------------------------------------------------------+ |
|         │                                                                                          |
|         ▼ Emits Normalized AST Facts (with start/end line, byte span, docstrings, def-use)         |
|  [Unified In-Memory Semantic Property Graph (NetworkX DiGraph) + Universal Namespace Isolation]   |
+----------------------------------------------------------------------------------------------------+
```

---

### 1.1 Detailed Polyglot Language Matrix (40+ Languages, 103+ File Extensions)

| # | Language / Platform | File Extensions | Grammar / Parsing Engine | Facts & Entities Extracted |
|---|---|---|---|---|
| **1** | **Python** | `.py` | Stdlib `ast` + `tree-sitter-python` | Classes, functions, async defs, decorators, docstrings, calls, imports, def-use variables, raises/handles blocks, rationale comments. |
| **2** | **TypeScript & JavaScript** | `.ts`, `.tsx`, `.mts`, `.cts`, `.js`, `.jsx`, `.mjs`, `.cjs`, `.ejs`, `.ets` | `tree-sitter-typescript`, `tree-sitter-javascript` | Classes, interfaces, types, functions, methods, arrow funcs, imports/exports, dynamic `import()`, `require()`, API client calls (`fetch`, `axios`). |
| **3** | **Vue.js** | `.vue` | `extract_vue` + script masking | Extracts `<script>` and `<script setup>` JS/TS blocks; maps template bindings to script variables. |
| **4** | **Svelte** | `.svelte` | `extract_svelte` + script masking | Extracts `<script>` JS/TS blocks, reactive `$:` declarations, store subscriptions, and exported component props. |
| **5** | **Astro** | `.astro` | `extract_astro` + frontmatter parser | Extracts frontmatter JS/TS code blocks, component imports, and props interfaces. |
| **6** | **Go** | `.go` | `tree-sitter-go` | Structs, interfaces, methods with receiver types, package imports, functions, goroutines, predeclared funcs, type references. |
| **7** | **Rust** | `.rs` | `tree-sitter-rust` + `cargo_introspect.py` | Structs, enums, traits, `impl` blocks, functions, macros, `use` statements, Cargo workspace dependency trees. |
| **8** | **Java** | `.java` | `tree-sitter-java` | Classes, interfaces, enums, records, methods, annotations, package hierarchy, cross-file type imports, inheritance. |
| **9** | **Groovy & Gradle** | `.groovy`, `.gradle` | `tree-sitter-groovy` | Script tasks, plugin blocks, closures, class definitions, method invocations, dependency declarations. |
| **10** | **Kotlin** | `.kt`, `.kts` | `tree-sitter-kotlin` | Classes, data classes, interfaces, extension functions, companion objects, package declarations, type references. |
| **11** | **Scala** | `.scala` | `tree-sitter-scala` | Classes, case classes, traits, objects, package objects, methods, type aliases, inheritance. |
| **12** | **C** | `.c`, `.h` | `tree-sitter-c` | Functions, struct definitions, enum definitions, typedefs, preprocessor `#include` directives, macros. |
| **13** | **C++** | `.cpp`, `.cc`, `.cxx`, `.hpp` | `tree-sitter-cpp` | Classes, structs, namespaces, template classes, template functions, method declaration/definition merging (`_merge_decl_def_classes`). |
| **14** | **CUDA** | `.cu`, `.cuh` | `tree-sitter-cpp` | Kernel declarations (`__global__`), device functions (`__device__`), host functions, CUDA memory transfers. |
| **15** | **Metal Shading Language** | `.metal` | `tree-sitter-cpp` | Compute kernels, vertex/fragment shaders, buffer bindings. |
| **16** | **C#** | `.cs` | `tree-sitter-c-sharp` + `csharp_dispatch.py` | Classes, records, interfaces, structs, properties, methods, namespaces, interface dispatch resolution, cross-file imports. |
| **17** | **VB.NET** | `.vb` | `tree-sitter-vb-dotnet` (`vbnet.py`) | Modules, classes, structures, interfaces, Sub/Function declarations, partial classes, cross-file method resolution. |
| **18** | **Razor / Blazor** | `.razor`, `.cshtml` | `razor.py` | `@code` C# blocks, component directives, HTML tag helpers, component hierarchies. |
| **19** | **XAML** | `.xaml` | `extract_xaml` | Element hierarchy, user control bindings, `x:Class` code-behind links, event handler connections. |
| **20** | **.NET Solution / Projects** | `.sln`, `.slnx`, `.csproj`, `.fsproj`, `.vbproj` | `sln.py`, `csproj` extractors | Inter-project dependencies, project-to-project references, assembly metadata. |
| **21** | **Swift** | `.swift` | `tree-sitter-swift` + `swift_dispatch.py` | Classes, structs, protocols, extensions, functions, properties, protocol dispatch resolution, module imports. |
| **22** | **Objective-C / Obj-C++** | `.m`, `.mm` | `tree-sitter-objc` (`objc.py`) | `@interface`, `@implementation`, `@protocol`, categories, message sending expressions (`[obj message]`). |
| **23** | **Ruby** | `.rb`, `.rake` | `tree-sitter-ruby` + `ruby_resolution.py` | Classes, modules, methods, singleton methods, `require`/`require_relative`, dynamic class factories (`Class.new`), member calls. |
| **24** | **PHP** | `.php` | `tree-sitter-php` | Classes, interfaces, traits, namespaces, functions, methods, use imports, type references. |
| **25** | **Laravel Blade** | `.blade.php` | `blade.py` | `@component`, `@include`, `@extends`, `@section` directives and template dependencies. |
| **26** | **Lua & Luau** | `.lua`, `.luau`, `.toc` | `tree-sitter-lua` | Functions, tables, local/global variable assignments, `require()` module target resolution, WoW addon TOC files. |
| **27** | **Zig** | `.zig` | `tree-sitter-zig` (`zig.py`) | Structs, enums, unions, error sets, functions, `@import` declarations, test blocks. |
| **28** | **PowerShell** | `.ps1`, `.psm1`, `.psd1` | `tree-sitter-powershell` (`powershell.py`) | Functions, filters, Cmdlets, script blocks, module manifests (`.psd1`), exported functions/aliases. |
| **29** | **Bash / POSIX Shell** | `.sh`, `.bash` | `tree-sitter-bash` (`bash.py`) | Functions, script definitions, `source` / `.` inclusions, executable script-to-script dispatches (`EXECUTES`). |
| **30** | **Elixir** | `.ex`, `.exs` | `tree-sitter-elixir` (`elixir.py`) | Modules (`defmodule`), functions (`def`, `defp`), macros (`defmacro`), aliases, imports, pipe chains (`|>`). |
| **31** | **Erlang** | `.erl`, `.hrl`, `.escript` | `tree-sitter-language-pack` (`erlang.py`) | Modules, exported functions, records (`-record`), header inclusions (`-include`), remote function calls (`M:F(A)`). |
| **32** | **Dart** | `.dart` | `dart.py` | Classes, abstract classes, mixins, extension methods, constructors, Flutter widget declarations, imports. |
| **33** | **R** | `.r`, `.R` | `tree-sitter-language-pack` (`r.py`) | Function definitions, S3/S4 methods, library declarations (`library()`, `require()`), `source()` file calls. |
| **34** | **Julia** | `.jl` | `tree-sitter-julia` (`julia.py`) | Modules, structs, functions, multiple dispatch method signatures, macros, `using`/`import` statements. |
| **35** | **OCaml** | `.ml`, `.mli` | `tree-sitter-ocaml` (`ocaml.py`) | Modules, module types (`sig`), values (`val`), `let` bindings, type declarations, `open` statements. |
| **36** | **Common Lisp** | `.lisp`, `.cl`, `.lsp`, `.asd` | `tree-sitter-commonlisp` (`commonlisp.py`) | Functions (`defun`), macros (`defmacro`), classes (`defclass`), methods (`defmethod`), ASDF system definitions (`.asd`). |
| **37** | **Fortran** | `.f`, `.F`, `.f90`, `.F90`, `.f95`, `.f03`, `.f08` | `tree-sitter-fortran` (`fortran.py`) + CPP | Programs, modules, subroutines, functions, `USE` statements, CPP preprocessing for capitalized extensions. |
| **38** | **Pascal / Delphi / Lazarus** | `.pas`, `.pp`, `.dpr`, `.dpk`, `.lpr`, `.inc`, `.dfm`, `.lfm`, `.lpk` | `tree-sitter-pascal` / regex fallback (`pascal.py`, `pascal_forms.py`) | Units, programs, interfaces, implementation sections, classes, methods, inherited calls, visual form visual components. |
| **39** | **COBOL** | `.cbl`, `.cob`, `.cobol`, `.cpy` | `cobol.py` | Identification, Data, and Procedure divisions, sections, paragraphs, copybooks (`COPY`), `PERFORM` call statements. |
| **40** | **Salesforce Apex** | `.cls`, `.trigger` | `apex.py` | Classes, interfaces, triggers (`trigger on Account`), SOQL database queries (`[SELECT ...]`), DML statements (`insert`, `update`). |
| **41** | **Solidity** | `.sol` | `tree-sitter-solidity` (`solidity.py`) | Contracts, interfaces, libraries, modifiers, events, functions, inheritance, constructor calls, type references. |
| **42** | **Verilog & SystemVerilog** | `.v`, `.sv`, `.svh`, `.vh` | `tree-sitter-verilog` (`verilog.py`) | Modules, tasks, functions, ports, module instances, header inclusions (`include`). |
| **43** | **BYOND DreamMaker** | `.dm`, `.dme`, `.dmi`, `.dmm`, `.dmf` | `tree-sitter-dm` (`dm.py`) | Object type paths (`/obj/item`), procs, verbs, map files (`.dmm`), interface descriptors (`.dmf`), environment files (`.dme`). |
| **44** | **Robot Framework** | `.robot`, `.resource` | `robotframework` API (`robot.py`) | Test suites, test cases, user keywords, library imports, resource file references. |
| **45** | **Terraform / HCL** | `.tf`, `.tfvars`, `.hcl` | `tree-sitter-hcl` (`terraform.py`) | Resources, data sources, modules, variables, locals, outputs, module invocations. |
| **46** | **SQL & Databases** | `.sql` | `tree-sitter-sql` + `sqlglot` | DDL tables, views, primary/foreign keys, DML def-use flows (`SELECT` -> `READS`, `INSERT`/`UPDATE` -> `WRITES`). |
| **47** | **Config & Manifests** | `.json`, `.yaml`, `.yml`, `.toml` | Stdlib `json`, `pyyaml`, `tomli` | Package manifests (`package.json`, `Cargo.toml`, `pyproject.toml`), MCP configs, environment configs. |
| **48** | **Docs & Media** | `.md`, `.mdx`, `.qmd`, `.skill`, `.docx`, `.xlsx`, `.pdf` | `markdown.py`, `pypdf`, `python-docx` | Headings, wikilinks, inter-document mentions, slide notes, workbook sheets, PDF chapters. |

---

### 1.2 Shebang Dispatch for Extensionless Executables (`_SHEBANG_DISPATCH`)
To handle repository root scripts, CLI entrypoints, and DevOps utilities that lack file extensions (e.g. `devctl`, `run`, `manage`), RepoPeek inspects the file shebang line:
```python
_SHEBANG_DISPATCH = {
    "python": extract_python,
    "python2": extract_python,
    "python3": extract_python,
    "bash": extract_bash,
    "sh": extract_bash,
    "dash": extract_bash,
    "zsh": extract_bash,
    "ksh": extract_bash,
    "node": extract_js,
    "nodejs": extract_js,
    "ruby": extract_ruby,
    "lua": extract_lua,
    "php": extract_php,
    "julia": extract_julia,
    "Rscript": extract_r,
}
```

---

## 2. Cross-Language Boundary Bridges

A core limitation of traditional code graphs is that they terminate at language boundaries. RepoPeek implements four deterministic bridging engines to establish cross-boundary traversals.

### 2.1 Cross-Language HTTP Boundary Bridge (`repopeek.bridges.http`)
Connects frontend/client API calls to backend route handlers across any language pair:
- **Client Extraction:** Identifies API requests from TypeScript, JavaScript, Dart (Flutter), Swift (iOS), Kotlin (Android):
  - `fetch("/api/v1/invoices/" + id, { method: "POST" })`
  - `axios.get("/api/v1/users/:userId/roles")`
  - `http.get(Uri.parse('$baseUrl/items/$id'))`
- **Server Route Extraction:** Identifies backend endpoints from Python (FastAPI, Flask, Django), Node.js (Express, NestJS), Go (Gin, Chi, standard net/http), Java (Spring Boot `@GetMapping`), C# (ASP.NET `[HttpGet]`), Ruby (Rails routes):
  - `@router.get("/api/v1/invoices/{invoice_id}")`
  - `r.GET("/api/v1/users/:userId/roles", Handler)`
  - `@GetMapping("/items/{id}")`
- **Path Parameter Normalization:**
  All path parameter representations (`:param`, `{param}`, `<param>`, numeric regexes) are normalized to canonical `:param`:
  ```
  Client: /api/v1/invoices/:id        ──┐
                                         ├──> Match! Synthesizes INVOKES edge
  Server: /api/v1/invoices/{invoice_id}──┘    with confidence 0.75 (INFERRED)
  ```
- **Trailing Slash & Prefix Tolerance:** Suffix matching and basePath proxy prefix matching resolve relative paths.

### 2.2 SQL Data Flow Bridge (`repopeek.bridges.sql`)
- Connects application code data layers (Python SQLAlchemy, TS Prisma/TypeORM, Go GORM, Java Hibernate/JPA, Rust Diesel/SQLx) to database schema entities.
- Identifies raw SQL strings and table names (e.g. `__tablename__ = "invoices"`, `Table("invoices")`).
- Connects application functions directly to `sql:table.invoices` via `READS` or `WRITES` edges.

### 2.3 Subprocess Bridge (`repopeek.bridges.process`)
- Connects high-level orchestrators (Python `subprocess.run`, Node `child_process.exec`, Go `exec.Command`, Rust `Command::new`) to shell execution pipelines.
- When Python code executes `subprocess.run(["./scripts/migrate.sh", "--apply"])`, RepoPeek synthesizes an `EXECUTES` edge between the calling Python method and the target Shell script file node.

### 2.4 Configuration Key Bridge (`repopeek.bridges.config`)
- Binds code environment accesses (`os.getenv("PAYMENT_GATEWAY_URL")`, `process.env.PAYMENT_GATEWAY_URL`, `os.Getenv(...)`) to the YAML/JSON configuration declarations defining `PAYMENT_GATEWAY_URL`.

---

## 3. Universal Namespace Isolation & Collision Guard (All 40+ Languages)

### The Polyglot Collision Hazard
During real-world benchmarking on fullstack multi-language repositories, unnamespaced identifier matching led to catastrophic graph explosions. For example:
- A TypeScript frontend imported the package `'next'` (Next.js router).
- A Python backend invoked Python's built-in iterator function `next()`.
- A C# worker invoked a class member `Next()`.
- A flat property graph merged all three entities into a single node with ID `"next"`.
- A blast-radius query traversed across disconnected runtimes, yielding **190,000+ lines of irrelevant graph JSON** across 800+ nodes.

### RepoPeek Universal Namespace Protocol
RepoPeek mandates explicit, non-overlapping runtime prefixes for every node in the graph across all supported languages:

| Prefix | Domain / Language Family | Example Node ID |
|---|---|---|
| `py:` | Python application code | `py:services/invoice.py::InvoiceParser.parse` |
| `ts:` | TypeScript / JavaScript / SFC | `ts:src/components/InvoiceView.tsx::InvoiceCard` |
| `go:` | Go packages & structs | `go:pkg/server/handler.go::Server.HandleInvoice` |
| `rs:` | Rust crates & modules | `rs:src/engine.rs::Engine::execute` |
| `java:` | Java packages & classes | `java:com.example.service::InvoiceService.process` |
| `kt:` | Kotlin classes & functions | `kt:app.model::Order.calculateTotal` |
| `scala:` | Scala objects & traits | `scala:org.repo.core::Pipeline.run` |
| `groovy:` | Groovy & Gradle tasks | `groovy:build.gradle::task.compileApp` |
| `c:` | C functions & structs | `c:src/parser.c::parse_token` |
| `cpp:` | C++ / CUDA / Metal classes & templates | `cpp:include/kernel.cu::cuda_matrix_mult` |
| `cs:` | C# classes, interfaces & records | `cs:Services/Billing.cs::IBillingService.Bill` |
| `vb:` | VB.NET modules & classes | `vb:ModMain.vb::Module1.Main` |
| `swift:` | Swift protocols & classes | `swift:Sources/UI/View.swift::AppCoordinator` |
| `objc:` | Objective-C interfaces & categories | `objc:Classes/Worker.m::Worker.startTask` |
| `rb:` | Ruby classes & modules | `rb:app/models/user.rb::User#authenticate` |
| `php:` | PHP classes, traits & functions | `php:src/Controllers/Auth.php::AuthController` |
| `lua:` | Lua / Luau functions & tables | `lua:scripts/game.lua::EntityManager.spawn` |
| `zig:` | Zig structs & functions | `zig:src/main.zig::Allocator.alloc` |
| `sh:` | Bash / POSIX Shell scripts & functions | `sh:scripts/deploy.sh::run_docker` |
| `ps:` | PowerShell functions & Cmdlets | `ps:tools/setup.ps1::Invoke-BuildStep` |
| `ex:` | Elixir modules & functions | `ex:lib/server.ex::Server.handle_call` |
| `erl:` | Erlang modules & functions | `erl:src/gen_worker.erl::worker:start_link` |
| `dart:` | Dart / Flutter widgets & classes | `dart:lib/main.dart::HomeScreenState.build` |
| `r:` | R functions & scripts | `r:scripts/analysis.R::calculate_p_values` |
| `jl:` | Julia modules & functions | `jl:src/solver.jl::solve_system` |
| `ml:` | OCaml modules & values | `ml:src/parser.ml::Parser.eval_expr` |
| `lisp:` | Common Lisp functions & macros | `lisp:src/core.lisp::defun_process_batch` |
| `f:` | Fortran modules & subroutines | `f:src/math.f90::matrix_inversion` |
| `pas:` | Pascal / Delphi units & procedures | `pas:units/db.pas::TDatabase.Connect` |
| `cbl:` | COBOL divisions & paragraphs | `cbl:src/PAYROLL.cbl::PROCESS-SALARY` |
| `apex:` | Salesforce Apex classes & triggers | `apex:classes/AccountTrigger.cls::onInsert` |
| `sol:` | Solidity contracts & functions | `sol:contracts/Vault.sol::Vault.deposit` |
| `v:` | Verilog / SystemVerilog modules | `v:hdl/alu.v::alu_core` |
| `dm:` | BYOND DreamMaker procs & atoms | `dm:code/mob.dm::/mob/proc/login` |
| `tf:` | Terraform / HCL resources & modules | `tf:main.tf::resource.aws_s3_bucket.data` |
| `robot:` | Robot Framework test cases & keywords | `robot:tests/login.robot::ValidLoginKeyword` |
| `sql:` | SQL tables, views & stored procedures | `sql:schema.sql::table.invoices` |
| `cfg:` | Configuration keys & blocks | `cfg:config.yaml::database.port` |
| `doc:` | Markdown documentation & skills | `doc:docs/ARCHITECTURE.md#pipeline` |
| `npm:` | External NPM package dependencies | `npm:next`, `npm:axios`, `npm:react` |
| `pip:` | External Python PyPI dependencies | `pip:fastapi`, `pip:pydantic`, `pip:numpy` |
| `cargo:` | External Rust Cargo crates | `cargo:tokio`, `cargo:serde` |
| `nuget:` | External .NET NuGet packages | `nuget:Microsoft.EntityFrameworkCore` |
| `gomod:` | External Go modules | `gomod:github.com/gin-gonic/gin` |
| `builtin:` | Standard library built-ins | `builtin:py:next`, `builtin:js:Array.map` |

*Invariant:* Traversal algorithms strictly enforce boundary crossing validation. A step between different language domains is permitted **only** across an explicit bridge edge (`INVOKES`, `EXECUTES`, `READS`, `WRITES`), completely preventing lexical collisions across all 40+ languages.

---

## 4. The 9 Deterministic Materialized Lenses

Rather than presenting agents with an undifferentiated graph of everything, RepoPeek computes 9 focused graph projections on demand across all 40+ languages:

```
+----------------------------------------------------------------------------------------------------+
| 9 DETERMINISTIC LENSES                                                                             |
|                                                                                                    |
| 1. Module Lens     - Directory hierarchy, file modules, package layout (CONTAINS).                 |
| 2. Symbol Lens     - Functions, classes, interfaces, variables, types (DEFINES).                   |
| 3. Call Lens       - Function invocations, method calls, HTTP API invocations (CALLS, INVOKES).   |
| 4. Class Lens      - Class inheritance, interface implementations, mixins (INHERITS, IMPLEMENTS).  |
| 5. Data Lens       - Def-use flows, variable and entity state changes (READS, WRITES).             |
| 6. Entity Lens     - Database tables, schemas, ORM models, persistent entities (REFERENCES).       |
| 7. Config Lens     - Settings, env flags, YAML/JSON application parameters (CONFIGURES).          |
| 8. Process Lens    - Subprocess execution, CLI commands, shell workflows (EXECUTES).              |
| 9. Exception Lens  - Error propagation, raise sites, try-catch handling blocks (RAISES, HANDLES).   |
+----------------------------------------------------------------------------------------------------+
```

### Lens Projection Specification Table

| Lens ID | Primary Nodes Included | Primary Edges Included | Use Case for Coding Agent |
|---|---|---|---|
| `Module` | Directories, Files (all 40+ languages) | `CONTAINS`, `IMPORTS` | High-level repo navigation and subsystem scoping |
| `Symbol` | Classes, Functions, Interfaces, Types, Structs, Traits | `DEFINES`, `EXPORTS` | Symbol resolution and declaration location lookup |
| `Call` | Functions, Methods, Routes, Kernels, Procs | `CALLS`, `INVOKES` | Call-chain tracing and upstream caller impact analysis |
| `Class` | Classes, Interfaces, Protocols, Structs, Traits | `INHERITS`, `IMPLEMENTS` | OOP hierarchy refactoring and polymorphism inspection |
| `Data` | Functions, Variables, Tables, State Fields | `READS`, `WRITES` | State mutation tracking and data race debugging |
| `Entity` | SQL Tables, Views, ORM Models, Schemas | `REFERENCES`, `FOREIGN_KEY` | Database schema migrations and data model reasoning |
| `Config` | Config Keys, Application Functions, TF Variables | `CONFIGURES`, `READS` | Environment variable updates and feature flag audit |
| `Process` | Shell Scripts, Orchestrators, CLI Entrypoints | `EXECUTES` | CI/CD pipelines, container build scripts, CLI dispatches |
| `Exception` | Functions, Exception Classes, Error Types | `RAISES`, `HANDLES` | Error handling verification and crash blast radius |

### On-Demand Lens Filtering Algorithm
Each node and edge stores a bitmask or set of matching lens labels. When an agent queries a specific lens (e.g. `--lens Data` or MCP tool filter), the SQLite query or in-memory subgraph view filters instantaneously without full graph recomputation:
```python
def project_lens(G: nx.DiGraph, lens_name: str) -> nx.DiGraph:
    """Extracts a sub-projection containing only nodes and edges tagged with the target lens."""
    sub_nodes = [n for n, d in G.nodes(data=True) if lens_name in d.get("lenses", [])]
    sub_G = G.subgraph(sub_nodes).copy()
    edges_to_remove = [
        (u, v) for u, v, d in sub_G.edges(data=True) if lens_name not in d.get("lenses", [])
    ]
    sub_G.remove_edges_from(edges_to_remove)
    return sub_G
```
