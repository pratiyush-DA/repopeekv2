"""Polyglot AST extraction engine and universal namespace adapter across all 40+ languages."""
from __future__ import annotations

import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

# Ensure Reference/graphify is on sys.path for downstream imports
_GRAPHIFY_REF = Path(__file__).resolve().parent.parent / "Reference" / "graphify"
if _GRAPHIFY_REF.is_dir() and str(_GRAPHIFY_REF) not in sys.path:
    sys.path.insert(0, str(_GRAPHIFY_REF))

try:
    from graphify.extract import _DISPATCH, _SHEBANG_DISPATCH, _safe_extract
except ImportError:
    _DISPATCH = {}
    _SHEBANG_DISPATCH = {}
    def _safe_extract(extractor: Callable, path: Path, **kwargs: Any) -> dict:
        return {"nodes": [], "edges": []}

from repopeek.detect import get_shebang_extension
from repopeek.models import EdgeRecord, NodeRecord

# Universal language namespace prefix map
EXTENSION_TO_PREFIX: dict[str, str] = {
    ".py": "py:",
    ".ts": "ts:", ".tsx": "ts:", ".mts": "ts:", ".cts": "ts:",
    ".js": "ts:", ".jsx": "ts:", ".mjs": "ts:", ".cjs": "ts:",
    ".vue": "ts:", ".svelte": "ts:", ".astro": "ts:", ".ejs": "ts:", ".ets": "ts:",
    ".go": "go:",
    ".rs": "rs:",
    ".java": "java:",
    ".kt": "kt:", ".kts": "kt:",
    ".scala": "scala:",
    ".groovy": "groovy:", ".gradle": "groovy:",
    ".c": "c:", ".h": "c:",
    ".cpp": "cpp:", ".cc": "cpp:", ".cxx": "cpp:", ".hpp": "cpp:",
    ".cu": "cpp:", ".cuh": "cpp:", ".metal": "cpp:",
    ".cs": "cs:",
    ".vb": "vb:",
    ".swift": "swift:",
    ".m": "objc:", ".mm": "objc:",
    ".rb": "rb:", ".rake": "rb:",
    ".php": "php:",
    ".lua": "lua:", ".luau": "lua:", ".toc": "lua:",
    ".zig": "zig:",
    ".sh": "sh:", ".bash": "sh:",
    ".ps1": "ps:", ".psm1": "ps:", ".psd1": "ps:",
    ".ex": "ex:", ".exs": "ex:",
    ".erl": "erl:", ".hrl": "erl:", ".escript": "erl:",
    ".dart": "dart:",
    ".r": "r:",
    ".jl": "jl:",
    ".ml": "ml:", ".mli": "ml:",
    ".lisp": "lisp:", ".cl": "lisp:", ".lsp": "lisp:", ".asd": "lisp:",
    ".f": "f:", ".F": "f:", ".f90": "f:", ".F90": "f:", ".f95": "f:", ".f03": "f:", ".f08": "f:",
    ".pas": "pas:", ".pp": "pas:", ".dpr": "pas:", ".dpk": "pas:", ".lpr": "pas:",
    ".inc": "pas:", ".dfm": "pas:", ".lfm": "pas:", ".lpk": "pas:",
    ".cbl": "cbl:", ".cob": "cbl:", ".cobol": "cbl:", ".cpy": "cbl:",
    ".cls": "apex:", ".trigger": "apex:",
    ".sol": "sol:",
    ".v": "v:", ".sv": "v:", ".svh": "v:", ".vh": "v:",
    ".dm": "dm:", ".dme": "dm:", ".dmi": "dm:", ".dmm": "dm:", ".dmf": "dm:",
    ".tf": "tf:", ".tfvars": "tf:", ".hcl": "tf:",
    ".robot": "robot:", ".resource": "robot:",
    ".sql": "sql:",
    ".json": "cfg:", ".yaml": "cfg:", ".yml": "cfg:",
    ".md": "doc:", ".mdx": "doc:", ".qmd": "doc:", ".skill": "doc:",
}

_LINE_LOC_RE = re.compile(r"^L(\d+)(?:-(\d+))?$")


def get_namespace_prefix(path: Path) -> str:
    """Returns universal prefix for a file based on suffix or shebang."""
    suffix = path.suffix.lower()
    if suffix in EXTENSION_TO_PREFIX:
        return EXTENSION_TO_PREFIX[suffix]
    shebang_ext = get_shebang_extension(path)
    if shebang_ext and shebang_ext in EXTENSION_TO_PREFIX:
        return EXTENSION_TO_PREFIX[shebang_ext]
    return "repo:"


def apply_namespace(node_id: str, prefix: str) -> str:
    """Ensures a node ID has an explicit runtime prefix."""
    known_prefixes = (
        "py:", "ts:", "go:", "rs:", "java:", "kt:", "scala:", "groovy:",
        "c:", "cpp:", "cs:", "vb:", "swift:", "objc:", "rb:", "php:",
        "lua:", "zig:", "sh:", "ps:", "ex:", "erl:", "dart:", "r:",
        "jl:", "ml:", "lisp:", "f:", "pas:", "cbl:", "apex:", "sol:",
        "v:", "dm:", "tf:", "robot:", "sql:", "cfg:", "doc:", "repo:",
        "npm:", "pip:", "cargo:", "nuget:", "gomod:", "builtin:"
    )
    if any(node_id.startswith(p) for p in known_prefixes):
        return node_id
    return f"{prefix}{node_id}"


def parse_line_locations(source_loc: str | None) -> tuple[int, int]:
    """Parses 'L10' or 'L10-25' into (start_line, end_line)."""
    if not source_loc:
        return 1, 1
    m = _LINE_LOC_RE.match(source_loc)
    if m:
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start
        return start, end
    return 1, 1


def compute_byte_offsets(file_path: Path, start_line: int, end_line: int) -> tuple[int, int]:
    """Computes exact 0-indexed byte offsets for lines."""
    try:
        content = file_path.read_bytes()
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)
        if total_lines == 0:
            return 0, 0
        s_idx = max(0, min(start_line - 1, total_lines - 1))
        e_idx = max(s_idx, min(end_line - 1, total_lines - 1))
        start_byte = sum(len(lines[i]) for i in range(s_idx))
        end_byte = sum(len(lines[i]) for i in range(e_idx + 1))
        return start_byte, end_byte
    except (OSError, UnicodeDecodeError):
        return 0, 0


def assign_node_lenses(kind: str, node_id: str) -> set[str]:
    """Assigns matching 9 lens labels to an extracted node."""
    lenses = set()
    k = kind.lower()
    if k in ("file", "module", "package", "directory"):
        lenses.add("Module")
    if k in ("function", "method", "class", "interface", "type", "struct", "variable", "proc"):
        lenses.add("Symbol")
    if k in ("class", "interface", "trait", "protocol", "struct"):
        lenses.add("Class")
    if k in ("table", "view", "column", "schema"):
        lenses.add("Entity")
    if k in ("config_key", "config_block", "setting"):
        lenses.add("Config")
    if k in ("script", "command", "task", "job"):
        lenses.add("Process")
    if "exception" in k or "error" in k or "raises" in k:
        lenses.add("Exception")
    if not lenses:
        lenses.add("Symbol")
    return lenses


def assign_edge_lenses(relation: str) -> set[str]:
    """Assigns matching 9 lens labels to an extracted edge."""
    lenses = set()
    r = relation.upper()
    if r in ("CONTAINS", "IMPORTS", "INCLUDES"):
        lenses.add("Module")
    if r in ("DEFINES", "EXPORTS", "DECLARES"):
        lenses.add("Symbol")
    if r in ("CALLS", "INVOKES"):
        lenses.add("Call")
    if r in ("INHERITS", "IMPLEMENTS", "EXTENDS"):
        lenses.add("Class")
    if r in ("READS", "WRITES", "MUTATES"):
        lenses.add("Data")
    if r in ("REFERENCES", "FOREIGN_KEY"):
        lenses.add("Entity")
    if r in ("CONFIGURES", "BINDS"):
        lenses.add("Config")
    if r in ("EXECUTES", "DISPATCHES"):
        lenses.add("Process")
    if r in ("RAISES", "HANDLES", "THROWS", "CATCHES"):
        lenses.add("Exception")
    if not lenses:
        lenses.add("Symbol")
    return lenses


from repopeek.extractors.sql import extract_sql_glot


def extract_file(path: Path, root: Path | None = None) -> tuple[list[NodeRecord], list[EdgeRecord]]:
    """Extracts normalized NodeRecord and EdgeRecord tuples from a single file across 40+ languages."""
    suffix = path.suffix.lower()

    if suffix == ".sql":
        raw = extract_sql_glot(path)
    else:
        extractor = _DISPATCH.get(suffix)
        if not extractor and not suffix:
            shebang_ext = get_shebang_extension(path)
            if shebang_ext:
                interpreter = shebang_ext.lstrip(".")
                extractor = _SHEBANG_DISPATCH.get(interpreter) or _DISPATCH.get(shebang_ext)

        if not extractor:
            return [], []

        raw = _safe_extract(extractor, path, scan_root=root)
    prefix = get_namespace_prefix(path)
    nodes: list[NodeRecord] = []
    edges: list[EdgeRecord] = []

    try:
        rel_path = path.relative_to(root).as_posix() if root else path.as_posix()
    except ValueError:
        rel_path = path.as_posix()

    for n in raw.get("nodes", []):
        raw_id = n.get("id") or f"{rel_path}:{n.get('label', 'unnamed')}"
        node_id = apply_namespace(raw_id, prefix)
        kind = n.get("kind") or n.get("file_type") or "symbol"
        label = n.get("label") or node_id.split("::")[-1]
        start_line, end_line = parse_line_locations(n.get("source_location"))
        start_byte, end_byte = compute_byte_offsets(path, start_line, end_line)
        lenses = assign_node_lenses(kind, node_id)

        rec = NodeRecord(
            id=node_id,
            kind=kind,
            label=label,
            file_path=rel_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=start_byte,
            end_byte=end_byte,
            docstring=n.get("docstring") or n.get("rationale") or "",
            lenses=lenses,
            reads=n.get("reads", []),
            writes=n.get("writes", []),
            raises=n.get("raises", []),
            external=bool(n.get("external", False)),
            metadata={k: v for k, v in n.items() if k not in ("id", "kind", "label", "docstring", "reads", "writes", "raises")}
        )
        nodes.append(rec)

    for e in raw.get("edges", []):
        src_raw = e.get("source")
        tgt_raw = e.get("target")
        if not src_raw or not tgt_raw:
            continue
        source_id = apply_namespace(src_raw, prefix)
        target_id = apply_namespace(tgt_raw, prefix)
        relation = e.get("relation") or e.get("type") or "DEPENDS_ON"
        conf_val = e.get("confidence", 1.0)
        if isinstance(conf_val, (int, float)):
            confidence = float(conf_val)
        elif isinstance(conf_val, str):
            conf_map = {"EXTRACTED": 1.0, "INFERRED": 0.75, "AMBIGUOUS": 0.5}
            confidence = conf_map.get(conf_val.strip().upper(), 1.0)
        else:
            confidence = 1.0
        lenses = assign_edge_lenses(relation)

        edge_rec = EdgeRecord(
            source=source_id,
            target=target_id,
            relation=relation,
            confidence=confidence,
            lenses=lenses,
            evidence=e.get("evidence") or e.get("source_location") or "",
            metadata={k: v for k, v in e.items() if k not in ("source", "target", "relation", "confidence")}
        )
        edges.append(edge_rec)

    return nodes, edges


def extract_repository(files: list[Path], root: Path | None = None) -> tuple[list[NodeRecord], list[EdgeRecord]]:
    """Extracts all files in a repository, returning complete lists of NodeRecord and EdgeRecord."""
    all_nodes: list[NodeRecord] = []
    all_edges: list[EdgeRecord] = []

    # Sequential extraction avoids multi-process IPC overhead on typical repos (<500 files)
    # and satisfies Ponytail's minimal complexity principle
    for f in files:
        nodes, edges = extract_file(f, root=root)
        all_nodes.extend(nodes)
        all_edges.extend(edges)

    return all_nodes, all_edges


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    test_file = Path("repopeek/models.py")
    nodes, edges = extract_file(test_file)
    assert len(nodes) > 0, "Expected non-zero nodes from repopeek/models.py"
    assert any(n.id.startswith("py:") for n in nodes), "Expected py: namespace prefix"
    assert any("Symbol" in n.lenses for n in nodes), "Expected Symbol lens assignment"
    print(f"repopeek.extract self-test passed! Extracted {len(nodes)} nodes, {len(edges)} edges.")
