"""Unit tests for polyglot AST fact extraction and namespace isolation in repopeek.extract."""
from pathlib import Path
import pytest

from repopeek.extract import (
    apply_namespace,
    compute_byte_offsets,
    extract_file,
    get_namespace_prefix,
    parse_line_locations,
)
from repopeek.models import EdgeRecord, NodeRecord


def test_namespace_prefix_resolution():
    assert get_namespace_prefix(Path("app.py")) == "py:"
    assert get_namespace_prefix(Path("component.tsx")) == "ts:"
    assert get_namespace_prefix(Path("handler.go")) == "go:"
    assert get_namespace_prefix(Path("engine.rs")) == "rs:"
    assert get_namespace_prefix(Path("Main.java")) == "java:"
    assert get_namespace_prefix(Path("server.cs")) == "cs:"
    assert get_namespace_prefix(Path("schema.sql")) == "sql:"
    assert get_namespace_prefix(Path("deploy.sh")) == "sh:"
    assert get_namespace_prefix(Path("config.yaml")) == "cfg:"


def test_apply_namespace_idempotent():
    assert apply_namespace("InvoiceParser", "py:") == "py:InvoiceParser"
    assert apply_namespace("py:InvoiceParser", "py:") == "py:InvoiceParser"
    assert apply_namespace("ts:Button", "py:") == "ts:Button"
    assert apply_namespace("npm:axios", "ts:") == "npm:axios"
    assert apply_namespace("pip:fastapi", "py:") == "pip:fastapi"


def test_line_location_parsing():
    assert parse_line_locations("L15") == (15, 15)
    assert parse_line_locations("L10-25") == (10, 25)
    assert parse_line_locations(None) == (1, 1)


def test_python_extraction_live():
    model_file = Path("repopeek/models.py")
    nodes, edges = extract_file(model_file)
    assert len(nodes) > 0
    assert len(edges) > 0
    
    # All nodes must have py: namespace prefix
    for n in nodes:
        assert n.id.startswith("py:")
        assert n.file_path.endswith("models.py")
        assert n.start_line > 0
        assert n.end_line >= n.start_line
        assert len(n.lenses) > 0

    # Verify specific model symbol extraction
    node_labels = {n.label for n in nodes}
    assert "NodeRecord" in node_labels or any("NodeRecord" in n.id for n in nodes)
    assert "EdgeRecord" in node_labels or any("EdgeRecord" in n.id for n in nodes)


def test_polyglot_typescript_extraction(tmp_path: Path):
    ts_file = tmp_path / "invoiceService.ts"
    ts_file.write_text(
        "export interface Invoice {\n"
        "  id: string;\n"
        "  amount: number;\n"
        "}\n\n"
        "export function calculateTax(inv: Invoice): number {\n"
        "  return inv.amount * 0.15;\n"
        "}\n",
        encoding="utf-8"
    )

    nodes, edges = extract_file(ts_file)
    assert len(nodes) > 0
    for n in nodes:
        assert n.id.startswith("ts:")
        assert "invoiceService.ts" in n.file_path
        assert "Symbol" in n.lenses


def test_polyglot_sql_extraction(tmp_path: Path):
    sql_file = tmp_path / "schema.sql"
    sql_file.write_text(
        "CREATE TABLE invoices (\n"
        "  id VARCHAR(64) PRIMARY KEY,\n"
        "  amount DECIMAL(10, 2)\n"
        ");\n",
        encoding="utf-8"
    )

    nodes, edges = extract_file(sql_file)
    assert len(nodes) > 0
    for n in nodes:
        assert n.id.startswith("sql:")


def test_byte_offset_calculation(tmp_path: Path):
    sample = tmp_path / "sample.py"
    sample.write_bytes(b"line1\nline2\nline3\n")
    start_byte, end_byte = compute_byte_offsets(sample, 2, 2)
    assert start_byte == 6  # len("line1\n")
    assert end_byte == 12   # len("line1\nline2\n")
