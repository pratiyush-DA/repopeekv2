"""Pull Request impact assessment, review queue triage, and community conflict detector."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import networkx as nx


def get_git_changed_files(repo_path: Path | str, base_branch: str = "main") -> list[str]:
    """Retrieves list of files modified on the current branch compared to base_branch."""
    try:
        cmd = ["git", "diff", "--name-only", f"{base_branch}...HEAD"]
        proc = subprocess.run(cmd, cwd=str(repo_path), capture_output=True, text=True, check=True)
        files = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        if not files:
            # Fallback to unstaged + staged files
            cmd2 = ["git", "status", "--porcelain"]
            proc2 = subprocess.run(cmd2, cwd=str(repo_path), capture_output=True, text=True, check=True)
            files = [line[3:].strip() for line in proc2.stdout.splitlines() if line.strip()]
        return files
    except Exception:
        return []


def analyze_pr_impact(
    graph: nx.DiGraph,
    changed_files: list[str],
) -> dict[str, Any]:
    """Computes architectural blast radius and touched communities for a set of changed files."""
    norm_changed = {Path(f).as_posix().lower() for f in changed_files}

    # 1. Collect directly modified nodes
    modified_nodes: list[str] = []
    touched_communities: set[int] = set()

    for n, data in graph.nodes(data=True):
        fp = Path(data.get("file_path", "")).as_posix().lower()
        if any(cf in fp or fp in cf for cf in norm_changed if cf):
            modified_nodes.append(n)
            touched_communities.add(data.get("community", 0))

    # 2. Find external callers (upstream blast radius)
    external_callers: list[dict[str, Any]] = []
    visited_callers: set[str] = set()

    for n in modified_nodes:
        for u, _, edata in graph.in_edges(n, data=True):
            if u not in modified_nodes and u not in visited_callers:
                visited_callers.add(u)
                u_data = graph.nodes[u]
                external_callers.append({
                    "caller_id": u,
                    "caller_label": u_data.get("label", u),
                    "file_path": u_data.get("file_path", ""),
                    "target_modified": n,
                    "relation": edata.get("relation", "DEPENDS_ON"),
                })

    # 3. Assess risk level
    is_god_node_touched = any(graph.degree(n) >= 15 for n in modified_nodes)
    if is_god_node_touched or len(external_callers) > 20 or len(touched_communities) > 3:
        risk = "HIGH"
    elif len(external_callers) >= 5 or len(touched_communities) > 1:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return {
        "changed_files_count": len(changed_files),
        "changed_files": changed_files,
        "modified_nodes_count": len(modified_nodes),
        "touched_communities": sorted(list(touched_communities)),
        "external_callers_count": len(external_callers),
        "external_callers": external_callers[:15],
        "risk_level": risk,
    }


def detect_branch_conflicts(
    graph: nx.DiGraph,
    branches_changed_files: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Detects architectural overlaps and semantic conflicts across concurrent branches."""
    branch_communities: dict[str, set[int]] = {}
    branch_nodes: dict[str, set[str]] = {}

    for branch_name, files in branches_changed_files.items():
        norm_files = {Path(f).as_posix().lower() for f in files}
        nodes = set()
        comms = set()

        for n, data in graph.nodes(data=True):
            fp = Path(data.get("file_path", "")).as_posix().lower()
            if any(cf in fp or fp in cf for cf in norm_files if cf):
                nodes.add(n)
                comms.add(data.get("community", 0))

        branch_nodes[branch_name] = nodes
        branch_communities[branch_name] = comms

    conflicts: list[dict[str, Any]] = []
    bnames = list(branches_changed_files.keys())

    for i in range(len(bnames)):
        for j in range(i + 1, len(bnames)):
            b1, b2 = bnames[i], bnames[j]
            overlap_comms = branch_communities[b1] & branch_communities[b2]
            overlap_nodes = branch_nodes[b1] & branch_nodes[b2]

            if overlap_comms or overlap_nodes:
                conflicts.append({
                    "branch_a": b1,
                    "branch_b": b2,
                    "overlapping_nodes": list(overlap_nodes),
                    "overlapping_communities": sorted(list(overlap_comms)),
                    "conflict_risk": "HIGH" if overlap_nodes else "MEDIUM",
                })

    return conflicts


def format_pr_dashboard(pr_impact: dict[str, Any]) -> str:
    """Formats markdown PR triage report."""
    lines = [
        "## RepoPeek Pull Request Impact Analysis",
        f"Assessed Risk: **[{pr_impact['risk_level']}]**",
        "",
        "### Overview:",
        f"- Changed Files: {pr_impact['changed_files_count']}",
        f"- Directly Modified Symbols: {pr_impact['modified_nodes_count']}",
        f"- Touched Communities: {pr_impact['touched_communities']}",
        f"- Upstream External Callers Affected: {pr_impact['external_callers_count']}",
    ]

    if pr_impact["external_callers"]:
        lines.append("\n### Key Callers at Risk of Breakage:")
        for c in pr_impact["external_callers"][:8]:
            lines.append(f"- `{c['caller_label']}` in `{c['file_path']}` (targets `{c['target_modified']}`)")

    return "\n".join(lines)
