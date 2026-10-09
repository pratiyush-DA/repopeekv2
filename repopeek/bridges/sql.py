"""SQL Data Def-Use Bridge connecting application code to database table nodes."""
from __future__ import annotations

import networkx as nx
from typing import Any

from repopeek.models import EdgeRecord


def synthesize_sql_bridges(graph: nx.DiGraph) -> list[EdgeRecord]:
    """Binds application code reads and writes facts to database table nodes."""
    # Index all table nodes in the graph
    table_nodes: dict[str, str] = {}  # table_name.lower() -> node_id
    for node_id, data in graph.nodes(data=True):
        kind = data.get("kind", "").lower()
        if kind in ("table", "view") or "table." in node_id:
            raw_name = node_id.split("table.")[-1].split("view.")[-1].split("::")[-1]
            table_nodes[raw_name.lower()] = node_id
            # Also register node's display label
            label = data.get("label", "").lower()
            if label:
                table_nodes[label] = node_id

    bridges: list[EdgeRecord] = []

    for node_id, data in graph.nodes(data=True):
        # Skip table nodes themselves
        if node_id in table_nodes.values():
            continue

        reads = [r.lower() for r in data.get("reads", [])]
        writes = [w.lower() for w in data.get("writes", [])]

        # Check ORM metadata
        meta = data.get("metadata", {})
        orm_table = meta.get("tablename") or meta.get("__tablename__")
        if orm_table:
            writes.append(str(orm_table).lower())

        for tbl in reads:
            if tbl in table_nodes:
                target_table = table_nodes[tbl]
                edge = EdgeRecord(
                    source=node_id,
                    target=target_table,
                    relation="READS",
                    confidence=0.85,
                    lenses={"Data", "Entity"},
                    evidence=f"Application function {node_id} reads SQL table {tbl}"
                )
                bridges.append(edge)
                graph.add_edge(
                    node_id,
                    target_table,
                    relation="READS",
                    confidence=0.85,
                    lenses={"Data", "Entity"},
                    evidence=edge.evidence,
                    metadata={}
                )

        for tbl in writes:
            if tbl in table_nodes:
                target_table = table_nodes[tbl]
                edge = EdgeRecord(
                    source=node_id,
                    target=target_table,
                    relation="WRITES",
                    confidence=0.85,
                    lenses={"Data", "Entity"},
                    evidence=f"Application function {node_id} mutates SQL table {tbl}"
                )
                bridges.append(edge)
                graph.add_edge(
                    node_id,
                    target_table,
                    relation="WRITES",
                    confidence=0.85,
                    lenses={"Data", "Entity"},
                    evidence=edge.evidence,
                    metadata={}
                )

    return bridges


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    G = nx.DiGraph()
    G.add_node("sql:schema.sql::table.invoices", kind="table", label="invoices")
    G.add_node("py:billing.py::create_invoice", kind="function", writes=["invoices"])
    G.add_node("py:reports.py::get_invoices", kind="function", reads=["invoices"])

    bridges = synthesize_sql_bridges(G)
    assert len(bridges) == 2, "Expected 2 SQL def-use bridge edges"
    assert G.has_edge("py:billing.py::create_invoice", "sql:schema.sql::table.invoices")
    assert G.has_edge("py:reports.py::get_invoices", "sql:schema.sql::table.invoices")
    assert G.edges["py:billing.py::create_invoice", "sql:schema.sql::table.invoices"]["relation"] == "WRITES"
    assert G.edges["py:reports.py::get_invoices", "sql:schema.sql::table.invoices"]["relation"] == "READS"
    print("repopeek.bridges.sql self-test passed!")
