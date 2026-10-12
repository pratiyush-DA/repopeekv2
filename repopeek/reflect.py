"""Experiential work-memory reflection, outcome tracking, and learning overlay."""
from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import networkx as nx

OUTCOMES = ("useful", "dead_end", "corrected")


def save_result(
    repopeek_dir: Path | str,
    question: str,
    answer: str,
    outcome: str = "useful",
    nodes: list[str] | None = None,
    correction: str = "",
) -> Path:
    """Records an experiential Q&A outcome in .repopeek/memory/."""
    if outcome not in OUTCOMES:
        raise ValueError(f"Invalid outcome '{outcome}'. Expected one of {OUTCOMES}.")

    base = Path(repopeek_dir).resolve()
    mem_dir = base / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)

    event_id = uuid.uuid4().hex[:12]
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "id": event_id,
        "timestamp": now_iso,
        "question": question,
        "answer": answer,
        "outcome": outcome,
        "nodes": nodes or [],
        "correction": correction,
    }

    out_file = mem_dir / f"result_{event_id}.json"
    out_file.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return out_file


def reflect(
    repopeek_dir: Path | str,
    graph: nx.DiGraph | None = None,
    out_markdown: Path | str = "docs/LESSONS.md",
    half_life_days: float = 30.0,
    min_corroboration: int = 2,
) -> dict[str, Any]:
    """Aggregates memory outcomes, calculates time-decayed node scores, and synthesizes LESSONS.md."""
    base = Path(repopeek_dir).resolve()
    mem_dir = base / "memory"
    out_md_path = Path(out_markdown).resolve()
    out_md_path.parent.mkdir(parents=True, exist_ok=True)

    if not mem_dir.exists():
        return {
            "total_memories": 0,
            "preferred_nodes": [],
            "contested_nodes": [],
            "dead_ends": [],
            "lessons_path": str(out_md_path),
        }

    now = datetime.now(timezone.utc)
    node_scores: dict[str, float] = {}
    node_positive_hits: dict[str, int] = {}
    node_negative_hits: dict[str, int] = {}
    dead_ends: list[dict[str, Any]] = []
    corrections: list[dict[str, Any]] = []
    total_memories = 0

    for file_path in mem_dir.glob("result_*.json"):
        try:
            rec = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        total_memories += 1
        created_at = datetime.fromisoformat(rec.get("timestamp", now.isoformat()))
        days_ago = max(0.0, (now - created_at).total_seconds() / 86400.0)
        decay = math.pow(0.5, days_ago / half_life_days)

        outcome = rec.get("outcome", "useful")
        cited_nodes = rec.get("nodes", [])

        if outcome == "useful":
            for n in cited_nodes:
                node_scores[n] = node_scores.get(n, 0.0) + (1.0 * decay)
                node_positive_hits[n] = node_positive_hits.get(n, 0) + 1
        elif outcome == "dead_end":
            dead_ends.append(rec)
            for n in cited_nodes:
                node_scores[n] = node_scores.get(n, 0.0) - (1.0 * decay)
                node_negative_hits[n] = node_negative_hits.get(n, 0) + 1
        elif outcome == "corrected":
            corrections.append(rec)
            for n in cited_nodes:
                node_scores[n] = node_scores.get(n, 0.0) - (1.5 * decay)
                node_negative_hits[n] = node_negative_hits.get(n, 0) + 1

    # Classify nodes
    preferred: list[str] = []
    tentative: list[str] = []
    contested: list[str] = []

    for n, score in node_scores.items():
        pos = node_positive_hits.get(n, 0)
        neg = node_negative_hits.get(n, 0)
        if pos >= min_corroboration and neg == 0:
            preferred.append(n)
        elif pos > 0 and neg > 0:
            contested.append(n)
        elif pos == 1 and neg == 0:
            tentative.append(n)

    # Render LESSONS.md
    lines = [
        "# Architectural Lessons & Experiential Work Memory",
        "",
        f"*Synthesized on {now.strftime('%Y-%m-%d %H:%M:%S UTC')} from {total_memories} recorded agent outcomes.*",
        "",
        "## 1. Preferred High-Confidence Sources (Corroborated)",
    ]

    if not preferred:
        lines.append("- *No sources corroborated with multiple positive validations yet.*")
    else:
        for p in sorted(preferred):
            lbl = graph.nodes[p].get("label", p) if graph and p in graph else p
            lines.append(f"- **`{lbl}`** (`{p}`): Score +{node_scores[p]:.2f}")

    lines.append("\n## 2. Contested Sources (Mixed Outcomes)")
    if not contested:
        lines.append("- *No contested or disputed sources.*")
    else:
        for c in sorted(contested):
            lbl = graph.nodes[c].get("label", c) if graph and c in graph else c
            lines.append(f"- **`{lbl}`** (`{c}`): Net Score {node_scores[c]:.2f} (Pos: {node_positive_hits.get(c, 0)}, Neg: {node_negative_hits.get(c, 0)})")

    lines.append("\n## 3. Known Dead Ends & Avoided Traps")
    if not dead_ends:
        lines.append("- *No recorded dead ends.*")
    else:
        for de in dead_ends[:10]:
            lines.append(f"- **Avoid**: Question: *'{de.get('question')}'* led to dead-end answer.")

    if corrections:
        lines.append("\n## 4. User Corrections & Truth Alignments")
        for corr in corrections[:10]:
            lines.append(f"- Question: *'{corr.get('question')}'*\n  - Correction: {corr.get('correction')}")

    lines.append("\n---\n*RepoPeek V2 Experiential Reflection Engine.*")
    out_md_path.write_text("\n".join(lines), encoding="utf-8")

    # Write learning sidecar
    sidecar_data = {
        "version": 1,
        "timestamp": now.isoformat(),
        "preferred": preferred,
        "tentative": tentative,
        "contested": contested,
        "scores": node_scores,
    }
    (base / ".repopeek_learning.json").write_text(json.dumps(sidecar_data, indent=2), encoding="utf-8")

    return {
        "total_memories": total_memories,
        "preferred_nodes": preferred,
        "tentative_nodes": tentative,
        "contested_nodes": contested,
        "dead_ends_count": len(dead_ends),
        "corrections_count": len(corrections),
        "lessons_path": str(out_md_path),
    }
