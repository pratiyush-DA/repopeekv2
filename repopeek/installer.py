"""Automated AI assistant skill and MCP configuration installer for RepoPeek."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SUPPORTED_PLATFORMS = ("claude-code", "cursor", "antigravity", "copilot", "all")

REPOPEEK_MCP_DEF = {
    "command": "repopeek",
    "args": ["--serve-mcp", "--repo-path", "."],
}


def _update_json_mcp(file_path: Path, server_key: str = "repopeek") -> bool:
    """Safely updates or creates an MCP JSON configuration file."""
    data: dict[str, Any] = {}
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    if not isinstance(data, dict):
        data = {}

    mcp_servers = data.setdefault("mcpServers", {})
    if not isinstance(mcp_servers, dict):
        mcp_servers = {}
        data["mcpServers"] = mcp_servers

    mcp_servers[server_key] = REPOPEEK_MCP_DEF
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return True


def install_claude_code(repo_root: Path) -> list[str]:
    """Installs Claude Code MCP configuration."""
    mcp_path = repo_root / ".mcp.json"
    _update_json_mcp(mcp_path)
    return [str(mcp_path)]


def install_cursor(repo_root: Path) -> list[str]:
    """Installs Cursor MCP configuration and rules."""
    created = []
    # 1. .cursor/mcp.json
    mcp_path = repo_root / ".cursor" / "mcp.json"
    _update_json_mcp(mcp_path)
    created.append(str(mcp_path))

    # 2. .cursor/rules/repopeek.mdc
    rules_dir = repo_root / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    rule_file = rules_dir / "repopeek.mdc"
    rule_content = """---
description: RepoPeek AST Code Property Graph & Token Efficiency Directives
globs: *
alwaysApply: true
---

# RepoPeek Intelligence Directives

This project is indexed by RepoPeek V2 Semantic Code Property Graph (SCPG).
Always use RepoPeek MCP tools to navigate and edit code efficiently:

1. **Before editing or exploring**: Call `repopeek_context(task="...")` to receive targeted <=4 file packages (~40 lines each) instead of dumping raw full files into context.
2. **Before refactoring**: Call `repopeek_impact(target="...")` to calculate exact upstream blast radius and affected callers.
3. **For symbols**: Call `repopeek_lookup(query="...")` for AST signatures and facts.
4. **For plans**: Call `repopeek_plan(task="...")` for step-by-step risk-assessed roadmaps.
"""
    with open(rule_file, "w", encoding="utf-8") as f:
        f.write(rule_content)
    created.append(str(rule_file))
    return created


def install_antigravity(repo_root: Path) -> list[str]:
    """Installs Google Antigravity / Hermes system rules."""
    rules_dir = repo_root / ".agents" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    rule_file = rules_dir / "repopeek.md"
    rule_content = """# RepoPeek Agent Directives

- **Code Property Graph Active**: This repository is indexed by RepoPeek V2.
- **Progressive Disclosure**: Call `repopeek_context` with progressive levels (level 1=orientation, level 2=focus, level 3=deep) to constrain context tokens by 90%+.
- **Blast Radius Verification**: Always run `repopeek_impact` before proposing structural code changes.
- **ROI Ledger**: Check token savings with `repopeek_savings` at the conclusion of tasks.
"""
    with open(rule_file, "w", encoding="utf-8") as f:
        f.write(rule_content)
    return [str(rule_file)]


def install_copilot(repo_root: Path) -> list[str]:
    """Installs GitHub Copilot workspace instructions."""
    github_dir = repo_root / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)
    inst_file = github_dir / "copilot-instructions.md"
    inst_content = """# GitHub Copilot Instructions for RepoPeek

- This codebase is analyzed by RepoPeek V2 Semantic Code Property Graph.
- For multi-file changes or impact analysis, run `repopeek --context "<task>"` and `repopeek --impact "<symbol>"` via CLI.
- Minimize unconstrained full-file reading by referencing RepoPeek AST fact cards.
"""
    with open(inst_file, "w", encoding="utf-8") as f:
        f.write(inst_content)
    return [str(inst_file)]


def install_platform(platform: str, repo_path: Path | str = ".") -> dict[str, Any]:
    """Installs assistant configurations for the specified platform."""
    repo_root = Path(repo_path).resolve()
    plat = platform.lower().strip()

    if plat not in SUPPORTED_PLATFORMS:
        raise ValueError(f"Unsupported platform '{platform}'. Supported platforms: {', '.join(SUPPORTED_PLATFORMS)}")

    files_created: list[str] = []
    if plat in ("claude-code", "all"):
        files_created.extend(install_claude_code(repo_root))
    if plat in ("cursor", "all"):
        files_created.extend(install_cursor(repo_root))
    if plat in ("antigravity", "all"):
        files_created.extend(install_antigravity(repo_root))
    if plat in ("copilot", "all"):
        files_created.extend(install_copilot(repo_root))

    return {
        "status": "success",
        "platform": plat,
        "repo_root": str(repo_root),
        "configured_files": files_created,
    }
