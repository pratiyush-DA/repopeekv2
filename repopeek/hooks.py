"""Git lifecycle hooks (post-commit, post-checkout) and automatic merge driver manager."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_HOOK_START = "# repopeek-hook-start"
_HOOK_END = "# repopeek-hook-end"

_HOOK_SCRIPT = f"""{_HOOK_START}
# Auto-update RepoPeek graph in background on git lifecycle events
python -m repopeek.cli --repo-path . > /dev/null 2>&1 &
{_HOOK_END}
"""


def get_git_dir(repo_path: Path | str) -> Path | None:
    """Finds the .git directory for a repository."""
    git_dir = Path(repo_path).resolve() / ".git"
    if git_dir.is_dir():
        return git_dir
    return None


def install_hooks(repo_path: Path | str) -> dict[str, str]:
    """Installs post-commit and post-checkout git hooks and configures merge driver."""
    git_dir = get_git_dir(repo_path)
    if not git_dir:
        return {"status": "error", "message": f"No .git directory found in {repo_path}"}

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    installed = []
    for hook_name in ("post-commit", "post-checkout"):
        hook_file = hooks_dir / hook_name
        current_content = hook_file.read_text(encoding="utf-8") if hook_file.exists() else ""

        if _HOOK_START not in current_content:
            new_content = current_content.rstrip() + "\n\n" + _HOOK_SCRIPT if current_content else "#!/bin/sh\n" + _HOOK_SCRIPT
            hook_file.write_text(new_content, encoding="utf-8")
            # Attempt to set executable bits on POSIX systems
            try:
                hook_file.chmod(hook_file.stat().st_mode | 0o111)
            except Exception:
                pass
            installed.append(hook_name)

    # Configure custom git merge driver
    try:
        subprocess.run(["git", "config", "merge.repopeek.name", "RepoPeek graph union merge"], cwd=str(repo_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "merge.repopeek.driver", f"{sys.executable} -m repopeek.cli --repo-path ."], cwd=str(repo_path), check=True, capture_output=True)
    except Exception:
        pass

    return {
        "status": "success",
        "installed_hooks": ", ".join(installed) if installed else "already_present",
        "merge_driver": "configured",
    }


def uninstall_hooks(repo_path: Path | str) -> bool:
    """Removes RepoPeek hook blocks from git hooks and resets merge driver."""
    git_dir = get_git_dir(repo_path)
    if not git_dir:
        return False

    hooks_dir = git_dir / "hooks"
    for hook_name in ("post-commit", "post-checkout"):
        hook_file = hooks_dir / hook_name
        if hook_file.exists():
            content = hook_file.read_text(encoding="utf-8")
            if _HOOK_START in content and _HOOK_END in content:
                # Strip out hook block
                before = content.split(_HOOK_START)[0]
                after = content.split(_HOOK_END)[1]
                cleaned = (before + after).strip()
                if cleaned in ("", "#!/bin/sh"):
                    hook_file.unlink(missing_ok=True)
                else:
                    hook_file.write_text(cleaned + "\n", encoding="utf-8")

    try:
        subprocess.run(["git", "config", "--unset", "merge.repopeek.name"], cwd=str(repo_path), capture_output=True)
        subprocess.run(["git", "config", "--unset", "merge.repopeek.driver"], cwd=str(repo_path), capture_output=True)
    except Exception:
        pass

    return True


def get_hook_status(repo_path: Path | str) -> dict[str, bool]:
    """Returns active status of git hooks and merge driver."""
    git_dir = get_git_dir(repo_path)
    if not git_dir:
        return {"post_commit": False, "post_checkout": False, "merge_driver": False}

    hooks_dir = git_dir / "hooks"
    pc = hooks_dir / "post-commit"
    pco = hooks_dir / "post-checkout"

    has_pc = pc.exists() and _HOOK_START in pc.read_text(encoding="utf-8", errors="ignore")
    has_pco = pco.exists() and _HOOK_START in pco.read_text(encoding="utf-8", errors="ignore")

    try:
        proc = subprocess.run(["git", "config", "merge.repopeek.name"], cwd=str(repo_path), capture_output=True, text=True)
        has_driver = bool(proc.stdout.strip())
    except Exception:
        has_driver = False

    return {
        "post_commit": has_pc,
        "post_checkout": has_pco,
        "merge_driver": has_driver,
    }
