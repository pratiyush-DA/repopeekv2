"""Cross-language boundary bridging engines."""
from __future__ import annotations

import networkx as nx

from repopeek.bridges.http import normalize_endpoint_path, synthesize_http_bridges
from repopeek.bridges.sql import synthesize_sql_bridges
from repopeek.models import EdgeRecord


def apply_all_bridges(graph: nx.DiGraph) -> list[EdgeRecord]:
    """Applies all cross-language bridges (HTTP routes, SQL def-use) to the graph."""
    all_bridges: list[EdgeRecord] = []
    all_bridges.extend(synthesize_http_bridges(graph))
    all_bridges.extend(synthesize_sql_bridges(graph))
    return all_bridges


__all__ = [
    "normalize_endpoint_path",
    "synthesize_http_bridges",
    "synthesize_sql_bridges",
    "apply_all_bridges",
]
