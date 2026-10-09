"""Canonical Semantic Code Property Graph (SCPG) assembly and graph building engine."""
from __future__ import annotations

import networkx as nx
from typing import Iterable

from repopeek.models import EdgeRecord, NodeRecord


def build_graph(nodes: Iterable[NodeRecord], edges: Iterable[EdgeRecord]) -> nx.DiGraph:
    """Assembles extracted NodeRecord and EdgeRecord collections into a canonical NetworkX DiGraph.
    
    Guarantees:
    - Directed arc order preserved.
    - External dependency stubs synthesized for dangling edge endpoints.
    - Node attributes preserved for surgical context extraction and lens projections.
    """
    G = nx.DiGraph()

    for n in nodes:
        G.add_node(
            n.id,
            id=n.id,
            label=n.label,
            kind=n.kind,
            file_path=n.file_path,
            start_line=n.start_line,
            end_line=n.end_line,
            start_byte=n.start_byte,
            end_byte=n.end_byte,
            docstring=n.docstring,
            lenses=set(n.lenses),
            reads=list(n.reads),
            writes=list(n.writes),
            raises=list(n.raises),
            external=n.external,
            metadata=dict(n.metadata),
        )

    for e in edges:
        # Synthesize external stub node if target does not exist in graph
        if e.target not in G:
            G.add_node(
                e.target,
                id=e.target,
                label=e.target.split("::")[-1].split(":")[-1],
                kind="external_stub",
                file_path="",
                start_line=0,
                end_line=0,
                start_byte=0,
                end_byte=0,
                docstring="External dependency stub",
                lenses={"Symbol"},
                reads=[],
                writes=[],
                raises=[],
                external=True,
                metadata={},
            )

        # Synthesize external stub node if source does not exist
        if e.source not in G:
            G.add_node(
                e.source,
                id=e.source,
                label=e.source.split("::")[-1].split(":")[-1],
                kind="external_stub",
                file_path="",
                start_line=0,
                end_line=0,
                start_byte=0,
                end_byte=0,
                docstring="External dependency stub",
                lenses={"Symbol"},
                reads=[],
                writes=[],
                raises=[],
                external=True,
                metadata={},
            )

        G.add_edge(
            e.source,
            e.target,
            relation=e.relation,
            confidence=e.confidence,
            lenses=set(e.lenses),
            evidence=e.evidence,
            metadata=dict(e.metadata),
        )

    return G


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    n1 = NodeRecord(
        id="py:main.py::run",
        kind="function",
        label="run",
        file_path="main.py",
        start_line=1,
        end_line=10,
        lenses={"Symbol", "Call"}
    )
    e1 = EdgeRecord(
        source="py:main.py::run",
        target="npm:axios",
        relation="CALLS",
        confidence=0.75,
        lenses={"Call"}
    )
    test_g = build_graph([n1], [e1])
    assert "py:main.py::run" in test_g, "Expected source node in graph"
    assert "npm:axios" in test_g, "Expected external stub node synthesized"
    assert test_g.nodes["npm:axios"]["external"] is True, "Expected stub to be external"
    assert test_g.has_edge("py:main.py::run", "npm:axios"), "Expected directed edge"
    print("repopeek.build self-test passed!")
