"""Tests for CLI flags and dispatch routing."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from repopeek.cli import main


def test_cli_hook_and_global_commands(tmp_path: Path):
    # Test --global-cmd list
    res = main(["--global-cmd", "list"])
    assert res == 0

    # Test --global-cmd path
    res = main(["--global-cmd", "path"])
    assert res == 0

    # Test --hook status
    res = main(["--repo-path", str(tmp_path), "--hook", "status"])
    assert res == 0

    # Test --hook install
    res = main(["--repo-path", str(tmp_path), "--hook", "install"])
    assert res == 0

    # Test --hook uninstall
    res = main(["--repo-path", str(tmp_path), "--hook", "uninstall"])
    assert res == 0


def test_cli_save_result_and_reflect(tmp_path: Path):
    # Test --save-result
    res = main([
        "--repo-path", str(tmp_path),
        "--save-result", "Where is auth handled?", "In auth/service.py", "useful"
    ])
    assert res == 0

    # Test --reflect
    res = main(["--repo-path", str(tmp_path), "--reflect"])
    assert res == 0
    lessons_file = tmp_path / "docs" / "LESSONS.md"
    assert lessons_file.exists()


def test_cli_indexing_and_prs(tmp_path: Path):
    # Create sample python file
    sample_py = tmp_path / "main.py"
    sample_py.write_text("def run():\n    pass\n", encoding="utf-8")

    # Run indexing with --diagnose
    res = main(["--repo-path", str(tmp_path), "--diagnose"])
    assert res == 0

    # Run indexing with --cycles
    res = main(["--repo-path", str(tmp_path), "--cycles"])
    assert res == 0

    # Run PRs impact analysis
    with patch("repopeek.cli.get_git_changed_files", return_value=["main.py"]):
        res = main(["--repo-path", str(tmp_path), "--prs"])
        assert res == 0
