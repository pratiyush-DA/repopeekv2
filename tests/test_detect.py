"""Unit tests for repository scanner and file classifier in repopeek.detect."""
import tempfile
from pathlib import Path
import pytest

from repopeek.detect import (
    CODE_EXTENSIONS,
    DOC_EXTENSIONS,
    classify_file,
    get_shebang_extension,
    is_ignored,
    scan_repository,
)
from repopeek.models import FileType


def test_code_extensions_count():
    assert len(CODE_EXTENSIONS) >= 100
    assert ".py" in CODE_EXTENSIONS
    assert ".ts" in CODE_EXTENSIONS
    assert ".rs" in CODE_EXTENSIONS
    assert ".go" in CODE_EXTENSIONS
    assert ".cpp" in CODE_EXTENSIONS
    assert ".cs" in CODE_EXTENSIONS
    assert ".cbl" in CODE_EXTENSIONS
    assert ".sol" in CODE_EXTENSIONS


def test_classification_by_extension():
    assert classify_file(Path("service.py")) == FileType.CODE
    assert classify_file(Path("app.tsx")) == FileType.CODE
    assert classify_file(Path("README.md")) == FileType.DOCUMENT
    assert classify_file(Path("paper.pdf")) == FileType.PAPER
    assert classify_file(Path("banner.png")) == FileType.IMAGE
    assert classify_file(Path("demo.mp4")) == FileType.VIDEO
    assert classify_file(Path("spec.docx")) == FileType.DOCUMENT


def test_shebang_classification(tmp_path: Path):
    script = tmp_path / "run_worker"
    script.write_text("#!/usr/bin/env python3\nprint('hello')\n", encoding="utf-8")
    assert get_shebang_extension(script) == ".py"
    assert classify_file(script) == FileType.CODE


def test_ignore_rules():
    assert is_ignored("node_modules/pkg/index.js", [])
    assert is_ignored("Reference/graphify/detect.py", [])
    assert is_ignored(".venv/bin/activate", [])
    assert is_ignored("build/lib.so", [])
    assert is_ignored("src/secret.key", ["*.key"])
    assert not is_ignored("src/billing/invoice.py", [])


def test_scan_repository_live():
    root = Path(".")
    discovered = scan_repository(root)
    assert FileType.CODE in discovered
    assert FileType.DOCUMENT in discovered
    # Ensure Reference/ is excluded from scan
    all_paths = [p.as_posix() for paths in discovered.values() for p in paths]
    assert not any("Reference/graphify" in p for p in all_paths)
