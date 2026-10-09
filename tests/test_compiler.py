"""Unit tests for Phase 4 Context Compiler, Change Planner, and AST Fact Verifier."""
from __future__ import annotations

from pathlib import Path
import tempfile
import networkx as nx
import pytest

from repopeek.context import (
    ContextCompiler,
    ChangePlanEngine,
    build_ast_fact_card,
    verify_story_claims,
)


def test_build_ast_fact_card():
    node = {
        "label": "compute_tax",
        "kind": "function",
        "file_path": "finance/tax.py",
        "start_line": 15,
        "end_line": 30,
        "docstring": "Calculates tax based on jurisdiction.",
        "reads": ["tax_rates"],
        "writes": ["tax_ledger"],
        "raises": ["InvalidJurisdictionError"],
        "lenses": {"Symbol", "Data"}
    }
    card = build_ast_fact_card(node)
    assert "compute_tax" in card
    assert "finance/tax.py" in card
    assert "tax_rates" in card
    assert "tax_ledger" in card
    assert "InvalidJurisdictionError" in card


def test_verify_story_claims():
    ast_facts = {
        "calls": ["validate_id", "fetch_db"],
        "writes": ["orders_table"],
        "reads": ["users_table"],
        "raises": ["ValidationError"],
    }

    # True story
    valid_story = {
        "claimed_calls": ["validate_id"],
        "claimed_writes": ["orders_table"],
        "claimed_reads": ["users_table"],
        "claimed_raises": ["ValidationError"],
    }
    valid, violations = verify_story_claims(valid_story, ast_facts)
    assert valid
    assert len(violations) == 0

    # Hallucinated story
    fake_story = {
        "claimed_calls": ["delete_all_records"],
        "claimed_writes": ["secret_passwords"],
    }
    valid, violations = verify_story_claims(fake_story, ast_facts)
    assert not valid
    assert len(violations) == 2


def test_context_compiler_strict_file_cap():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # Create 10 files
        G = nx.DiGraph()
        for i in range(10):
            fp = f"module_{i}.py"
            p = root / fp
            p.write_text(f"def action_{i}():\n    return {i}\n", encoding="utf-8")
            G.add_node(f"py:{fp}::action_{i}", label=f"action_{i}", kind="function", file_path=fp, start_line=1, end_line=2)

        compiler = ContextCompiler(root, G)

        # Query broad task that hits all
        pkg = compiler.compile_context("Update action functions across modules", level=2, max_files=4)
        assert pkg.file_count <= 4
        assert len(pkg.snippets) <= 4
        assert pkg.scorecard["files_avoided"] >= 6
        assert pkg.scorecard["tokens_saved"] > 0


def test_context_compiler_progressive_disclosure():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        p = root / "service.py"
        lines = [f"# line {i}" for i in range(100)]
        lines[20] = "def process_order():"
        lines[21] = "    return 'done'"
        p.write_text("\n".join(lines), encoding="utf-8")

        G = nx.DiGraph()
        G.add_node("py:service.py::process_order", label="process_order", kind="function", file_path="service.py", start_line=20, end_line=22)

        compiler = ContextCompiler(root, G)

        # Level 1: Orientation (~300 tokens, brief text)
        pkg_l1 = compiler.compile_context("Modify process_order", level=1)
        assert pkg_l1.level == 1
        assert "process_order" in pkg_l1.snippets[0].code_text
        assert "|" not in pkg_l1.snippets[0].code_text  # no line numbers formatted in level 1 orientation

        # Level 2: Focus Span (~40 lines)
        pkg_l2 = compiler.compile_context("Modify process_order", level=2)
        assert pkg_l2.level == 2
        assert "20 |" in pkg_l2.snippets[0].code_text


def test_change_plan_engine():
    G = nx.DiGraph()
    G.add_node("py:billing.py::charge_card", label="charge_card", kind="function", file_path="billing.py", writes=["payments"])
    G.add_node("py:api/checkout.py::checkout", label="checkout", kind="function", file_path="api/checkout.py")
    G.add_edge("py:api/checkout.py::checkout", "py:billing.py::charge_card", relation="CALLS")

    engine = ChangePlanEngine(".", G)
    plan = engine.generate_plan("Refactor charge_card payment flow")

    assert plan["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert plan["table_writes"] >= 1
    assert "charge_card" in plan["plan_markdown"]
    assert "## Step 1: Pre-flight Verification" in plan["plan_markdown"]
    assert "## Step 2: Implementation Sequence" in plan["plan_markdown"]
    assert "## Step 3: Database & State Entity Verification" in plan["plan_markdown"]
    assert "## Step 4: Synchronized Co-Change & Regression Testing" in plan["plan_markdown"]
