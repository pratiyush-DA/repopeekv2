"""AST Fact Verifier and Deterministic Fact Card Generator (Tier 1 & Tier 5)."""
from __future__ import annotations

from typing import Any


def build_ast_fact_card(node_data: dict[str, Any]) -> str:
    """Generates a zero-cost deterministic Markdown fact card directly from extracted AST attributes."""
    label = node_data.get("label", "unknown")
    kind = node_data.get("kind", "symbol")
    file_path = node_data.get("file_path", "")
    start_line = node_data.get("start_line", 1)
    end_line = node_data.get("end_line", 1)
    docstring = node_data.get("docstring", "").strip()

    reads = node_data.get("reads", [])
    writes = node_data.get("writes", [])
    raises = node_data.get("raises", [])
    lenses = node_data.get("lenses", [])
    if isinstance(lenses, (set, list)):
        lenses_str = ", ".join(sorted(lenses))
    else:
        lenses_str = str(lenses)

    lines = [
        f"### Symbol: `{label}` ({kind})",
        f"- **Location**: `{file_path}` (Lines {start_line}-{end_line})",
        f"- **Lenses**: {lenses_str or 'None'}",
    ]

    if docstring:
        lines.append(f"- **Docstring**: {docstring}")
    if reads:
        lines.append(f"- **Reads Entities**: {', '.join(reads)}")
    if writes:
        lines.append(f"- **Writes Entities**: {', '.join(writes)}")
    if raises:
        lines.append(f"- **Raises Exceptions**: {', '.join(raises)}")

    return "\n".join(lines)


def verify_story_claims(story: dict[str, Any], ast_facts: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validates that all entities and operations claimed in a summary exist in AST ground truth.
    
    Returns (is_valid, list_of_hallucination_violations).
    """
    violations: list[str] = []

    # 1. Verify claimed calls
    actual_calls = set(ast_facts.get("calls", []))
    for call in story.get("claimed_calls", []):
        if call not in actual_calls:
            violations.append(f"Hallucinated call: '{call}' not found in actual calls {sorted(actual_calls)}")

    # 2. Verify claimed database / variable writes
    actual_writes = set(ast_facts.get("writes", []))
    for write in story.get("claimed_writes", []):
        if write not in actual_writes:
            violations.append(f"Hallucinated write: '{write}' not found in actual writes {sorted(actual_writes)}")

    # 3. Verify claimed database / variable reads
    actual_reads = set(ast_facts.get("reads", []))
    for read in story.get("claimed_reads", []):
        if read not in actual_reads:
            violations.append(f"Hallucinated read: '{read}' not found in actual reads {sorted(actual_reads)}")

    # 4. Verify claimed raised exceptions
    actual_raises = set(ast_facts.get("raises", []))
    for r in story.get("claimed_raises", []):
        if r not in actual_raises:
            violations.append(f"Hallucinated exception: '{r}' not found in actual raises {sorted(actual_raises)}")

    is_valid = len(violations) == 0
    return is_valid, violations


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    node = {
        "label": "parse_invoice",
        "kind": "function",
        "file_path": "repopeek/parser.py",
        "start_line": 10,
        "end_line": 25,
        "docstring": "Parses invoices from PDF or XML.",
        "reads": ["invoices_raw"],
        "writes": ["invoices_table"],
        "raises": ["InvalidInvoiceError"],
        "lenses": {"Symbol", "Data"}
    }
    card = build_ast_fact_card(node)
    assert "parse_invoice" in card
    assert "invoices_table" in card

    ast_truth = {
        "calls": ["validate_checksum", "db_insert"],
        "writes": ["invoices_table"],
        "reads": ["invoices_raw"],
        "raises": ["InvalidInvoiceError"]
    }

    valid_story = {
        "claimed_calls": ["validate_checksum"],
        "claimed_writes": ["invoices_table"],
    }
    ok, errs = verify_story_claims(valid_story, ast_truth)
    assert ok, f"Expected valid story but got {errs}"

    fake_story = {
        "claimed_calls": ["non_existent_payment_gateway"],
        "claimed_writes": ["user_passwords"]
    }
    ok2, errs2 = verify_story_claims(fake_story, ast_truth)
    assert not ok2
    assert len(errs2) == 2
    print("repopeek.context.verifier self-test passed!")
