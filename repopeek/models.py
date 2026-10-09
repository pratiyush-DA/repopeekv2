"""Core data models and type contracts for RepoPeek V2."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class FileType(str, Enum):
    CODE = "code"
    DOCUMENT = "document"
    PAPER = "paper"
    IMAGE = "image"
    VIDEO = "video"


@dataclass(slots=True)
class NodeRecord:
    id: str
    kind: str
    label: str
    file_path: str
    start_line: int
    end_line: int
    start_byte: int = 0
    end_byte: int = 0
    docstring: str = ""
    lenses: set[str] = field(default_factory=set)
    reads: list[str] = field(default_factory=list)
    writes: list[str] = field(default_factory=list)
    raises: list[str] = field(default_factory=list)
    external: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["lenses"] = sorted(list(self.lenses))
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NodeRecord:
        d = dict(data)
        d["lenses"] = set(d.get("lenses", []))
        return cls(**d)


@dataclass(slots=True)
class EdgeRecord:
    source: str
    target: str
    relation: str
    confidence: float = 1.0
    lenses: set[str] = field(default_factory=set)
    evidence: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["lenses"] = sorted(list(self.lenses))
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EdgeRecord:
        d = dict(data)
        d["lenses"] = set(d.get("lenses", []))
        return cls(**d)


@dataclass(slots=True)
class ContextSnippet:
    file_path: str
    symbol_id: str
    start_line: int
    end_line: int
    code_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ContextPackage:
    task: str
    level: int
    file_count: int
    snippets: list[ContextSnippet]
    invariants: list[str]
    affected_tests: list[str]
    estimated_tokens: int
    scorecard: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "level": self.level,
            "file_count": self.file_count,
            "snippets": [s.to_dict() for s in self.snippets],
            "invariants": self.invariants,
            "affected_tests": self.affected_tests,
            "estimated_tokens": self.estimated_tokens,
            "scorecard": self.scorecard,
        }


@dataclass(slots=True)
class SavingsMetrics:
    baseline_tokens: int
    actual_tokens: int
    tokens_saved: int
    files_avoided: int
    cost_saved_usd: float
    cache_hit_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
