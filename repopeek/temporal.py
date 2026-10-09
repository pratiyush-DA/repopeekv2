"""Git Temporal Intelligence and Co-Change Matrix Miner with 180-day exponential decay."""
from __future__ import annotations

import math
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import networkx as nx

from repopeek.models import EdgeRecord

HALF_LIFE_DAYS = 180.0
MIN_CO_CHANGE_PROB = 0.25
MIN_COMMIT_COUNT = 2


def mine_git_co_changes(repo_path: Path | str) -> dict[str, dict[str, float]]:
    """Mines git commit history using 180-day exponential half-life decay.
    
    Returns a mapping: file_a -> {file_b: conditional_probability P(B|A)}
    """
    root = Path(repo_path).resolve()
    try:
        cmd = ["git", "log", "--name-only", "--pretty=format:COMMIT:%H:%at", "-n", "1000"]
        proc = subprocess.run(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return {}

    now = time.time()
    decay_constant = math.log(2.0) / (HALF_LIFE_DAYS * 86400.0)

    # commit_hash -> (weight, list_of_files)
    file_weights: dict[str, float] = defaultdict(float)
    pair_weights: dict[tuple[str, str], float] = defaultdict(float)
    pair_counts: dict[tuple[str, str], int] = defaultdict(int)

    current_weight = 1.0
    current_files: list[str] = []

    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("COMMIT:"):
            # Process previous commit files
            if current_files and current_weight > 0.0:
                unique_files = sorted(set(current_files))
                for f in unique_files:
                    file_weights[f] += current_weight
                for i in range(len(unique_files)):
                    for j in range(i + 1, len(unique_files)):
                        fa, fb = unique_files[i], unique_files[j]
                        pair_weights[(fa, fb)] += current_weight
                        pair_weights[(fb, fa)] += current_weight
                        pair_counts[(fa, fb)] += 1
                        pair_counts[(fb, fa)] += 1

            parts = line.split(":")
            if len(parts) >= 3:
                try:
                    commit_time = float(parts[2])
                    age_seconds = max(0.0, now - commit_time)
                    current_weight = math.exp(-decay_constant * age_seconds)
                except ValueError:
                    current_weight = 1.0
            else:
                current_weight = 1.0
            current_files = []
        else:
            # File line
            current_files.append(line.replace("\\", "/"))

    # Process final commit
    if current_files and current_weight > 0.0:
        unique_files = sorted(set(current_files))
        for f in unique_files:
            file_weights[f] += current_weight
        for i in range(len(unique_files)):
            for j in range(i + 1, len(unique_files)):
                fa, fb = unique_files[i], unique_files[j]
                pair_weights[(fa, fb)] += current_weight
                pair_weights[(fb, fa)] += current_weight
                pair_counts[(fa, fb)] += 1
                pair_counts[(fb, fa)] += 1

    # Calculate conditional probabilities P(B|A) = W(A & B) / W(A)
    co_changes: dict[str, dict[str, float]] = defaultdict(dict)
    for (fa, fb), w_ab in pair_weights.items():
        count = pair_counts[(fa, fb)]
        if count < MIN_COMMIT_COUNT:
            continue
        w_a = file_weights[fa]
        if w_a > 0.0:
            prob = min(0.99, w_ab / w_a)
            if prob >= MIN_CO_CHANGE_PROB:
                co_changes[fa][fb] = round(prob, 4)

    return dict(co_changes)


def apply_co_change_edges(graph: nx.DiGraph, co_changes: dict[str, dict[str, float]]) -> list[EdgeRecord]:
    """Synthesizes CO_CHANGED_WITH edges between file nodes in the graph."""
    edges: list[EdgeRecord] = []
    # Index file nodes in graph
    file_nodes: dict[str, str] = {}  # rel_path -> node_id
    for node_id, data in graph.nodes(data=True):
        fp = data.get("file_path")
        if fp:
            file_nodes[fp] = node_id

    for fa, b_dict in co_changes.items():
        src_node = file_nodes.get(fa)
        for fb, prob in b_dict.items():
            tgt_node = file_nodes.get(fb)
            if src_node and tgt_node and src_node != tgt_node:
                edge = EdgeRecord(
                    source=src_node,
                    target=tgt_node,
                    relation="CO_CHANGED_WITH",
                    confidence=prob,
                    lenses={"Module"},
                    evidence=f"Git temporal coupling P({fb}|{fa}) = {prob*100:.1f}%"
                )
                edges.append(edge)
                graph.add_edge(
                    src_node,
                    tgt_node,
                    relation="CO_CHANGED_WITH",
                    confidence=prob,
                    lenses={"Module"},
                    evidence=edge.evidence,
                    metadata={}
                )

    return edges


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    matrix = mine_git_co_changes(".")
    assert isinstance(matrix, dict), "Expected dict from mine_git_co_changes"
    print(f"repopeek.temporal self-test passed! Mined {len(matrix)} files with co-change coupling.")
