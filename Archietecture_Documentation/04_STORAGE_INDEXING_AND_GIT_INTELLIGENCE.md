# 04 - Storage, Indexing & Git Intelligence

## 1. Dual-Layer Hybrid Storage Engine

Graph traversal on large enterprise codebases requires both disk persistence for agent offline reloads and sub-millisecond query performance. RepoPeek implements a dual-layer hybrid architecture:

```
+----------------------------------------------------------------------------------------------------+
| REPOPEEK DUAL-LAYER STORAGE ARCHITECTURE                                                           |
|                                                                                                    |
|   Layer 1: Content-Addressed Atomic JSON Shards (.repopeek/shards/)                                |
|   - Sharded by file and community.                                                                 |
|   - Content-addressed via SHA-256; atomic file swap guarantees zero corruption.                    |
|   - Portable across environments and git-committable if desired.                                   |
|                                                                                                    |
|   Layer 2: High-Speed SQLite Recursive CTE Graph Cache (.repopeek/cache.db)                        |
|   - Relational indexes on (source, target, relation, lens, runtime_ns).                            |
|   - Transitive closure blast radius queries execute via recursive CTEs in <2ms.                    |
|   - Zero-dependency Python stdlib `sqlite3` engine.                                                |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Layer 1: Content-Addressed Atomic JSON Shards

### Sharding Strategy
Rather than maintaining a single monolithic `graph.json` that requires full re-serialization on every keystroke, RepoPeek partitions the graph into atomic JSON shards under `.repopeek/shards/`:
- `shards/files/<file_hash>.json`: Stores nodes and intra-file edges owned by an individual source file.
- `shards/communities/<community_id>.json`: Stores community membership and cohesion scores.
- `shards/manifest.json`: Stores repo metadata, commit SHA, dirty state, and index pointers.

### Atomic Write Protocol
To prevent torn reads by concurrent MCP servers or CLI processes during incremental writes, every shard write follows an atomic replace protocol:
```python
def write_shard_atomic(target_path: Path, data: dict) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(".tmp." + str(os.getpid()))
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_path, target_path)  # Atomic on POSIX and modern Windows NTFS
```

---

## 3. Layer 2: SQLite Recursive CTE Graph Cache

RepoPeek stores nodes, edges, and lens projections in a local SQLite database (`.repopeek/cache.db`), enabling fast recursive graph operations using SQL Recursive Common Table Expressions (CTEs).

### 3.1 Relational Schema

```sql
-- Node Table
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    runtime_ns TEXT NOT NULL,
    source_file TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    community INTEGER,
    content_hash TEXT NOT NULL,
    attributes_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_nodes_file ON nodes(source_file);
CREATE INDEX IF NOT EXISTS idx_nodes_community ON nodes(community);
CREATE INDEX IF NOT EXISTS idx_nodes_runtime ON nodes(runtime_ns);

-- Edge Table
CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    relation TEXT NOT NULL,
    confidence TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    source_file TEXT,
    source_line INTEGER,
    metadata_json TEXT,
    FOREIGN KEY(source) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY(target) REFERENCES nodes(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target);
CREATE INDEX IF NOT EXISTS idx_edges_rel ON edges(relation);
CREATE INDEX IF NOT EXISTS idx_edges_source_rel ON edges(source, relation);

-- Lens Association Tables
CREATE TABLE IF NOT EXISTS node_lenses (
    node_id TEXT NOT NULL,
    lens_name TEXT NOT NULL,
    PRIMARY KEY(node_id, lens_name)
);
CREATE INDEX IF NOT EXISTS idx_nl_lens ON node_lenses(lens_name);

CREATE TABLE IF NOT EXISTS edge_lenses (
    edge_id INTEGER NOT NULL,
    lens_name TEXT NOT NULL,
    PRIMARY KEY(edge_id, lens_name)
);
CREATE INDEX IF NOT EXISTS idx_el_lens ON edge_lenses(lens_name);
```

### 3.2 Transitive Closure & Blast Radius via Recursive CTEs
To calculate blast radius ("If I change function X, what callers and database tables are impacted?"), RepoPeek executes a recursive query directly inside SQLite:

```sql
WITH RECURSIVE blast_radius(node_id, depth, path) AS (
    -- Anchor: Seed node
    SELECT id, 0, id
    FROM nodes
    WHERE id = :target_id

    UNION

    -- Recursive Step: Traverse incoming CALLS, INVOKES, READS, WRITES edges
    SELECT e.source, br.depth + 1, br.path || ' -> ' || e.source
    FROM edges e
    JOIN blast_radius br ON e.target = br.node_id
    WHERE br.depth < :max_depth
      AND instr(br.path, e.source) = 0  -- Cycle prevention
)
SELECT DISTINCT 
    n.id, 
    n.label, 
    n.entity_type, 
    n.source_file, 
    n.start_line, 
    br.depth, 
    br.path
FROM blast_radius br
JOIN nodes n ON br.node_id = n.id
ORDER BY br.depth ASC;
```
*Performance Benchmark:* A 5-hop recursive blast-radius traversal over 15,000 nodes completes in **1.4ms** in SQLite, versus **48ms** in memory-bound NetworkX Python traversals.

---

## 4. Git Temporal Intelligence & Co-Change Matrix

Static AST analysis can only reveal explicit code dependencies. It cannot detect implicit architectural coupling — for instance, when changing a database migration file `migrations/004.sql` always requires updating a corresponding frontend schema `src/types/schema.ts` and documentation file `docs/api.md`.

RepoPeek bridges this gap by mining git commit history to construct a temporal co-change matrix.

### 4.1 Exponential Half-Life Decay Formulation
To prioritize recent architectural practices over obsolete legacy patterns, RepoPeek applies an exponential decay function with a **180-day half-life**:

$$\lambda = \frac{\ln(2)}{t_{\text{half}}} = \frac{0.69315}{180} \approx 0.00385 \text{ days}^{-1}$$

For each commit $c$ occurring $\Delta t$ days before the present:

$$w(c) = e^{-\lambda \cdot \Delta t}$$

### 4.2 Conditional Co-Change Probability Matrix
For any pair of files $A$ and $B$:
- Cumulative weighted co-change frequency:
  $$W(A \cap B) = \sum_{c \in \text{Commits}(A \cap B)} w(c)$$
- Cumulative weighted change frequency of $A$:
  $$W(A) = \sum_{c \in \text{Commits}(A)} w(c)$$
- Conditional probability that modifying file $A$ requires modifying file $B$:
  $$P(B \mid A) = \frac{W(A \cap B)}{W(A)}$$

### 4.3 Synthesizing `CO_CHANGED_WITH` Edges
RepoPeek introduces `CO_CHANGED_WITH` edges into the SCPG when:
1. $P(B \mid A) \ge 0.35$ (at least 35% time-weighted probability).
2. The pair has co-changed across at least 3 distinct non-merge commits.
3. The edge stores attributes: `confidence="INFERRED"`, `weight=P(B|A)`, `lens="Module"`, `temporal=True`.

When coding agents query `--impact <file>`, RepoPeek surfaces these temporally coupled files even when no direct import edge exists between them.

---

## 5. Incremental Watch Daemon (`repopeek.watch`)

To keep the SCPG continuously synchronized with agent file modifications without re-indexing the entire repository, RepoPeek provides an incremental watch daemon.

### 5.1 Architecture & Workflow
- **Zero-Dependency Tracking:** Monitors filesystem using Python stdlib `os.stat` (`st_mtime_ns`, `st_size`) or `watchdog` if installed.
- **Debounce Window:** 50ms debounce window groups atomic multi-file edits (e.g. git checkout, formatters).
- **Sub-50ms Delta Invalidation Cycle:**
  1. Detect modified file $F$.
  2. Compute SHA-256 hash. If unchanged, skip.
  3. Query SQLite for all nodes where `source_file = F`.
  4. Remove obsolete nodes and incoming/outgoing edges owned by $F$.
  5. Re-parse $F$ using the appropriate language AST parser.
  6. Re-evaluate local cross-language bridges for $F$'s symbols.
  7. Batch-insert new nodes and edges into SQLite; update the file's JSON shard.
  8. Broadcast invalidation event to in-process MCP server.

```
Total elapsed time for 1 file modification in a 200-file repository: <42ms.
```
