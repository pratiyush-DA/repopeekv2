"""Repository scanner, file type classifier, and discovery engine with full 40+ language support."""
from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path
from typing import Iterable

from repopeek.models import FileType

CODE_EXTENSIONS = {
    '.py', '.ts', '.tsx', '.mts', '.cts', '.js', '.jsx', '.mjs', '.cjs', '.ejs', '.ets',
    '.go', '.rs', '.vb', '.cbl', '.cob', '.cobol', '.cpy', '.java', '.groovy', '.gradle',
    '.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.cu', '.cuh', '.metal', '.rb', '.rake',
    '.swift', '.kt', '.kts', '.cs', '.scala', '.php', '.lua', '.luau', '.toc', '.zig',
    '.ps1', '.psm1', '.psd1', '.ex', '.exs', '.m', '.mm', '.ml', '.mli', '.jl',
    '.vue', '.svelte', '.astro', '.dart', '.v', '.sv', '.svh', '.vh', '.sql', '.r',
    '.f', '.F', '.f90', '.F90', '.f95', '.F95', '.f03', '.F03', '.f08', '.F08',
    '.pas', '.pp', '.dpr', '.dpk', '.lpr', '.inc', '.dfm', '.lfm', '.lpk',
    '.sh', '.bash', '.json', '.tf', '.tfvars', '.hcl',
    '.dm', '.dme', '.dmi', '.dmm', '.dmf',
    '.sln', '.slnx', '.csproj', '.fsproj', '.vbproj', '.xaml', '.razor', '.cshtml',
    '.cls', '.trigger', '.lisp', '.cl', '.lsp', '.asd', '.robot', '.resource',
    '.sol', '.erl', '.hrl', '.escript'
}

DOC_EXTENSIONS = {'.md', '.mdx', '.qmd', '.skill', '.txt', '.rst', '.html', '.yaml', '.yml'}
PAPER_EXTENSIONS = {'.pdf'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
OFFICE_EXTENSIONS = {'.docx', '.xlsx'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.webm', '.mkv', '.avi', '.m4v', '.mp3', '.wav', '.m4a', '.ogg'}

DEFAULT_IGNORED_DIRS = {
    '.git', '.svn', '.hg', '__pycache__', 'node_modules', '.venv', 'venv', 'env',
    'dist', 'build', '.eggs', '.pytest_cache', '.mypy_cache', '.ruff_cache',
    '.repopeek', 'graphify-out', 'Reference'
}

_SHEBANG_RE = re.compile(r"^#!\s*(?:/usr/bin/env\s+|/bin/|/usr/bin/)?([a-zA-Z0-9_\-\.]+)")

KNOWN_SHEBANGS = {
    "python": ".py",
    "python2": ".py",
    "python3": ".py",
    "node": ".js",
    "nodejs": ".js",
    "bash": ".sh",
    "sh": ".sh",
    "zsh": ".sh",
    "ruby": ".rb",
    "lua": ".lua",
    "php": ".php",
    "julia": ".jl",
    "Rscript": ".r",
}

_OFFICE_MAX_RAW_BYTES = 50 * 1024 * 1024
_OFFICE_MAX_DECOMPRESSED_BYTES = 512 * 1024 * 1024
CORPUS_WARN_FILE_COUNT = 500


def get_shebang_extension(path: Path) -> str | None:
    """Inspects first line for shebang interpreter to classify extensionless executable scripts."""
    try:
        if not path.is_file() or path.stat().st_size == 0 or path.stat().st_size > 2 * 1024 * 1024:
            return None
        with open(path, "rb") as f:
            first_line = f.readline().decode("utf-8", errors="ignore").strip()
            match = _SHEBANG_RE.match(first_line)
            if match:
                interpreter = match.group(1).lower()
                for key, ext in KNOWN_SHEBANGS.items():
                    if interpreter == key or interpreter.startswith(f"{key}."):
                        return ext
    except (OSError, UnicodeDecodeError):
        return None
    return None


def classify_file(path: Path) -> FileType | None:
    """Classifies file into FileType category using extension or shebang."""
    suffix = path.suffix.lower()
    if suffix in CODE_EXTENSIONS:
        return FileType.CODE
    if suffix in DOC_EXTENSIONS:
        return FileType.DOCUMENT
    if suffix in PAPER_EXTENSIONS:
        return FileType.PAPER
    if suffix in IMAGE_EXTENSIONS:
        return FileType.IMAGE
    if suffix in VIDEO_EXTENSIONS:
        return FileType.VIDEO
    if suffix in OFFICE_EXTENSIONS:
        return FileType.DOCUMENT
    
    # Check extensionless script via shebang
    if not suffix and get_shebang_extension(path) is not None:
        return FileType.CODE

    return None


def _load_ignore_patterns(root_path: Path) -> list[str]:
    """Loads patterns from .gitignore and .repopeekignore."""
    patterns = []
    for filename in (".gitignore", ".repopeekignore"):
        ignore_file = root_path / filename
        if ignore_file.is_file():
            try:
                for line in ignore_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                    clean = line.strip()
                    if clean and not clean.startswith("#"):
                        patterns.append(clean)
            except OSError:
                pass
    return patterns


def is_ignored(rel_path: str, patterns: list[str]) -> bool:
    """Determines whether a relative path matches ignore patterns or default ignored dirs."""
    parts = Path(rel_path).parts
    for part in parts:
        if part in DEFAULT_IGNORED_DIRS:
            return True

    for pattern in patterns:
        p = pattern.rstrip("/")
        if fnmatch.fnmatch(rel_path, p) or fnmatch.fnmatch(rel_path, f"{p}/*") or any(fnmatch.fnmatch(part, p) for part in parts):
            return True
    return False


def scan_repository(root: Path | str) -> dict[FileType, list[Path]]:
    """Recursively discovers and classifies repository files into FileType categories."""
    root_path = Path(root).resolve()
    patterns = _load_ignore_patterns(root_path)
    discovered: dict[FileType, list[Path]] = {t: [] for t in FileType}

    for current_dir, dirnames, filenames in os.walk(root_path):
        cur = Path(current_dir)
        try:
            rel_dir = cur.relative_to(root_path).as_posix()
        except ValueError:
            continue

        # Prune ignored directories in-place for performance
        dirnames[:] = [
            d for d in dirnames
            if d not in DEFAULT_IGNORED_DIRS and not is_ignored(f"{rel_dir}/{d}" if rel_dir != "." else d, patterns)
        ]

        for fname in filenames:
            rel_file = f"{rel_dir}/{fname}" if rel_dir != "." else fname
            if is_ignored(rel_file, patterns):
                continue
            
            file_path = cur / fname
            category = classify_file(file_path)
            if category is not None:
                discovered[category].append(file_path)

    return discovered


# Ponytail anti-hallucination verification block
if __name__ == "__main__":
    demo_py = Path("test_demo.py")
    assert classify_file(demo_py) == FileType.CODE, "Expected .py to be FileType.CODE"
    demo_doc = Path("notes.md")
    assert classify_file(demo_doc) == FileType.DOCUMENT, "Expected .md to be FileType.DOCUMENT"
    assert is_ignored("node_modules/pkg/index.js", []), "Expected node_modules to be ignored"
    assert is_ignored("Reference/graphify/detect.py", []), "Expected Reference to be ignored"
    print("detect.py self-test passed!")
