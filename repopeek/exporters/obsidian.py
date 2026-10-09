"""Obsidian Vault Exporter generating interconnected Markdown notes with YAML frontmatter and [[wikilinks]]."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import networkx as nx


def _sanitize_filename(name: str) -> str:
    """Sanitizes node identifier into a valid cross-platform file name."""
    clean = re.sub(r'[\\/*?:"<>|]', '_', name)
    return clean.strip(" ._")[:100]


def export_obsidian_vault(graph: nx.DiGraph, output_dir: Path | str) -> Path:
    """Exports the Semantic Code Property Graph into an Obsidian Markdown vault."""
    vault_path = Path(output_dir).resolve()
    obsidian_conf_dir = vault_path / ".obsidian"
    overview_dir = vault_path / "00_Overview"
    symbols_dir = vault_path / "Symbols"
    modules_dir = vault_path / "Modules"

    for d in (obsidian_conf_dir, overview_dir, symbols_dir, modules_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 1. Write .obsidian settings
    app_json = {"showLineNumber": True, "spellcheck": False}
    (obsidian_conf_dir / "app.json").write_text(json.dumps(app_json, indent=2), encoding="utf-8")

    graph_json = {
        "collapse-filter": True,
        "search": "",
        "localJumps": 1,
        "colorGroups": [
            {"query": "tag:#Lens_Call", "color": {"a": 1, "rgb": 5809919}},
            {"query": "tag:#Lens_Data", "color": {"a": 1, "rgb": 4176208}},
            {"query": "tag:#Lens_Module", "color": {"a": 1, "rgb": 15632948}},
        ]
    }
    (obsidian_conf_dir / "graph.json").write_text(json.dumps(graph_json, indent=2), encoding="utf-8")

    # 2. Export symbol and module notes
    node_to_filename: dict[str, str] = {}
    for n_id, data in graph.nodes(data=True):
        kind = data.get("kind", "symbol").lower()
        lbl = data.get("label", n_id)
        fname = _sanitize_filename(f"{lbl}_{n_id.split('::')[-1]}") or "node"
        node_to_filename[n_id] = fname

    communities: dict[int, list[str]] = {}

    for n_id, data in graph.nodes(data=True):
        fname = node_to_filename[n_id]
        kind = data.get("kind", "symbol").lower()
        is_module = kind in ("file", "module", "package")
        target_dir = modules_dir if is_module else symbols_dir
        note_file = target_dir / f"{fname}.md"

        comm = data.get("community", 0)
        communities.setdefault(comm, []).append(n_id)

        lenses = sorted(list(data.get("lenses", [])))
        lenses_yaml = "\n".join(f"  - {l}" for l in lenses) if lenses else "  - Symbol"
        tags_yaml = "\n".join(f"  - Lens_{l}" for l in lenses)

        # Frontmatter
        lines = [
            "---",
            f'id: "{n_id}"',
            f'label: "{data.get("label", n_id)}"',
            f'kind: "{kind}"',
            f'file_path: "{data.get("file_path", "")}"',
            f'start_line: {data.get("start_line", 1)}',
            f'end_line: {data.get("end_line", 1)}',
            f'community: {comm}',
            "lenses:",
            lenses_yaml,
            "tags:",
            tags_yaml,
            "---",
            "",
            f"# {data.get('label', n_id)}",
            "",
            f"> **Source:** `{data.get('file_path', '')}` (Lines {data.get('start_line', 1)}-{data.get('end_line', 1)})",
            f"> **Community:** [[_COMMUNITY_{comm}|Community {comm}]]",
            "",
        ]

        if data.get("docstring"):
            lines.extend([
                "## Documentation",
                data.get("docstring", "").strip(),
                "",
            ])

        # Outgoing edges
        out_edges = list(graph.out_edges(n_id, data=True))
        if out_edges:
            lines.append("## Outgoing Relationships")
            for _, v, edata in out_edges:
                rel = edata.get("relation", "DEPENDS_ON")
                v_fname = node_to_filename.get(v, _sanitize_filename(v))
                v_lbl = graph.nodes[v].get("label", v) if v in graph else v
                lines.append(f"- [[{rel}]] -> [[{v_fname}|{v_lbl}]]")
            lines.append("")

        # Incoming edges
        in_edges = list(graph.in_edges(n_id, data=True))
        if in_edges:
            lines.append("## Incoming Relationships")
            for u, _, edata in in_edges:
                rel = edata.get("relation", "DEPENDS_ON")
                u_fname = node_to_filename.get(u, _sanitize_filename(u))
                u_lbl = graph.nodes[u].get("label", u) if u in graph else u
                lines.append(f"- [[{rel}]] <- [[{u_fname}|{u_lbl}]]")
            lines.append("")

        note_file.write_text("\n".join(lines), encoding="utf-8")

    # 3. Write Master Index & Community Notes
    index_lines = [
        "# RepoPeek Knowledge Graph Index",
        "",
        f"- **Total Graph Nodes:** {graph.number_of_nodes()}",
        f"- **Total Graph Edges:** {graph.number_of_edges()}",
        f"- **Architectural Communities:** {len(communities)}",
        "",
        "## Architectural Subsystems (Communities)",
    ]
    for c_id, members in sorted(communities.items()):
        index_lines.append(f"- [[_COMMUNITY_{c_id}|Community {c_id}]] ({len(members)} nodes)")

        # Write individual community note
        comm_lines = [
            f"# Community {c_id} Architectural Subsystem",
            "",
            f"Total Symbols: {len(members)}",
            "",
            "## Constituent Symbols & Modules",
        ]
        for m_id in members[:50]:
            m_fname = node_to_filename[m_id]
            m_lbl = graph.nodes[m_id].get("label", m_id)
            comm_lines.append(f"- [[{m_fname}|{m_lbl}]] (`{m_id}`)")
        (overview_dir / f"_COMMUNITY_{c_id}.md").write_text("\n".join(comm_lines), encoding="utf-8")

    (overview_dir / "00_RepoPeek_Index.md").write_text("\n".join(index_lines), encoding="utf-8")

    return vault_path


# Ponytail anti-hallucination verification self-test
if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        G = nx.DiGraph()
        G.add_node("py:a.py::fn_a", label="fn_a", kind="function", file_path="a.py", lenses={"Symbol"})
        G.add_node("py:b.py::fn_b", label="fn_b", kind="function", file_path="b.py", lenses={"Symbol"})
        G.add_edge("py:a.py::fn_a", "py:b.py::fn_b", relation="CALLS")

        vault = export_obsidian_vault(G, Path(tmp_dir) / "obsidian_vault")
        assert (vault / "00_Overview" / "00_RepoPeek_Index.md").exists()
        assert (vault / ".obsidian" / "graph.json").exists()
        assert any((vault / "Symbols").iterdir())
        print("repopeek.exporters.obsidian self-test passed!")
