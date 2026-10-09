"""SQL parser and def-use extractor using SQLGlot (supporting Postgres, MySQL, Oracle, SQLite dialects)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import sqlglot
from sqlglot import exp


def extract_sql_glot(path: Path) -> dict[str, list[dict[str, Any]]]:
    """Extracts tables, views, columns, and DML READS/WRITES data flows from SQL source."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {"nodes": [], "edges": []}

    try:
        statements = sqlglot.parse(content)
    except Exception:
        # Fallback to loose regex or return empty on severe syntax errors
        return {"nodes": [], "edges": []}

    file_stem = path.stem
    rel_path = path.as_posix()

    for idx, stmt in enumerate(statements):
        if stmt is None:
            continue

        # DDL CREATE TABLE
        if isinstance(stmt, exp.Create):
            target = stmt.this
            if isinstance(target, exp.Schema):
                table_exp = target.this
            else:
                table_exp = target

            table_name = table_exp.name if hasattr(table_exp, "name") and table_exp.name else str(table_exp)
            if not table_name:
                continue

            is_view = stmt.args.get("kind") == "VIEW"
            kind = "view" if is_view else "table"
            node_id = f"table.{table_name}"
            
            # Extract column names if present
            columns = []
            if isinstance(target, exp.Schema):
                for col in target.expressions:
                    if isinstance(col, exp.ColumnDef):
                        columns.append(col.name)

            nodes.append({
                "id": node_id,
                "label": table_name,
                "kind": kind,
                "file_type": "code",
                "source_file": rel_path,
                "source_location": f"L{idx+1}",
                "docstring": f"SQL {kind.upper()} {table_name}",
                "metadata": {"columns": columns, "is_view": is_view}
            })

            # Check if view selects from other tables
            if is_view and stmt.expression:
                for table in stmt.expression.find_all(exp.Table):
                    src_table = table.name
                    if src_table and src_table != table_name:
                        edges.append({
                            "source": node_id,
                            "target": f"table.{src_table}",
                            "relation": "READS",
                            "confidence": 1.0,
                            "evidence": f"VIEW {table_name} selects from {src_table}"
                        })

        # DML INSERT / UPDATE / DELETE (WRITES)
        elif isinstance(stmt, (exp.Insert, exp.Update, exp.Delete)):
            table = stmt.find(exp.Table)
            if table and table.name:
                target_table = f"table.{table.name}"
                query_id = f"{file_stem}:stmt_{idx+1}"
                nodes.append({
                    "id": query_id,
                    "label": f"DML_{stmt.key.upper()}_{table.name}",
                    "kind": "query",
                    "source_file": rel_path,
                    "source_location": f"L{idx+1}",
                    "writes": [table.name]
                })
                edges.append({
                    "source": query_id,
                    "target": target_table,
                    "relation": "WRITES",
                    "confidence": 1.0,
                    "evidence": f"{stmt.key.upper()} into {table.name}"
                })
                # Check for SELECT inside INSERT (READS)
                for src_t in stmt.find_all(exp.Table):
                    if src_t.name and src_t.name != table.name:
                        edges.append({
                            "source": query_id,
                            "target": f"table.{src_t.name}",
                            "relation": "READS",
                            "confidence": 1.0,
                            "evidence": f"Read during {stmt.key.upper()}"
                        })

        # DML SELECT (READS)
        elif isinstance(stmt, exp.Select):
            for table in stmt.find_all(exp.Table):
                if table.name:
                    query_id = f"{file_stem}:select_{idx+1}"
                    nodes.append({
                        "id": query_id,
                        "label": f"SELECT_{table.name}",
                        "kind": "query",
                        "source_file": rel_path,
                        "source_location": f"L{idx+1}",
                        "reads": [table.name]
                    })
                    edges.append({
                        "source": query_id,
                        "target": f"table.{table.name}",
                        "relation": "READS",
                        "confidence": 1.0,
                        "evidence": f"SELECT query in {rel_path}"
                    })

    return {"nodes": nodes, "edges": edges}
