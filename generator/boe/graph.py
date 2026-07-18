"""networkx graph of relations among the state, counties, boards, and people.

The graph models Georgia's election-administration hierarchy as a directed
graph:

    state:GA ──contains──▶ county:{slug} ──has_board──▶ board:{id} ──has_member──▶ person:{id}

plus the reverse ``serves_on`` edge (person → board) for easy traversal from a
person up to their board. Node attributes carry the entity's data as JSON.

The graph is persisted to ``graph_nodes`` / ``graph_edges`` so it survives
across runs and can be queried without rebuilding it. ``build_graph`` always
reconstructs from the relational tables (source of truth); ``persist_graph``
is the explicit "save the current graph" call.
"""

from __future__ import annotations

import json

import networkx as nx

from .db import connect
from .repo import list_boards, list_counties, list_members

STATE_NODE = "state:GA"


def _node_id(node_type: str, key) -> str:
    return f"{node_type}:{key}"


def build_graph() -> nx.DiGraph:
    """Reconstruct the relations graph from the relational tables."""
    g: nx.DiGraph = nx.DiGraph()

    # The state node — everything hangs off it.
    g.add_node(STATE_NODE, node_type="state", name="Georgia", attrs={})

    counties = list_counties()
    boards = list_boards()
    members = list_members()

    county_by_id = {c.id: c for c in counties}

    for c in counties:
        nid = _node_id("county", c.slug)
        g.add_node(
            nid,
            node_type="county",
            name=c.name,
            attrs=c.model_dump(exclude_none=True),
        )
        g.add_edge(STATE_NODE, nid, relation="contains")

    for b in boards:
        nid = _node_id("board", b.id)
        g.add_node(
            nid,
            node_type="board",
            name=b.name,
            attrs=b.model_dump(exclude_none=True),
        )
        county = county_by_id.get(b.county_id)
        if county:
            g.add_edge(_node_id("county", county.slug), nid, relation="has_board")

    for m in members:
        nid = _node_id("person", m.id)
        g.add_node(
            nid,
            node_type="person",
            name=m.name,
            attrs=m.model_dump(exclude_none=True),
        )
        # person serves on their board (and board has them as a member)
        g.add_edge(nid, _node_id("board", m.board_id), relation="serves_on")
        g.add_edge(_node_id("board", m.board_id), nid, relation="has_member")

    return g


def persist_graph(g: nx.DiGraph) -> tuple[int, int]:
    """Write the graph to ``graph_nodes`` / ``graph_edges`` (replace all).

    Returns ``(nodes_written, edges_written)``.
    """
    with connect() as conn:
        conn.execute("DELETE FROM graph_nodes")
        conn.execute("DELETE FROM graph_edges")
        for nid, data in g.nodes(data=True):
            attrs = {k: v for k, v in data.items() if k not in ("node_type", "name")}
            conn.execute(
                "INSERT OR REPLACE INTO graph_nodes (node_id, node_type, name, attrs) "
                "VALUES (?, ?, ?, ?)",
                (nid, data.get("node_type"), data.get("name"), json.dumps(attrs, default=str)),
            )
        for u, v, data in g.edges(data=True):
            attrs = {k: val for k, val in data.items() if k != "relation"}
            conn.execute(
                "INSERT OR REPLACE INTO graph_edges (src, tgt, relation, attrs) VALUES (?, ?, ?, ?)",
                (u, v, data.get("relation", ""), json.dumps(attrs, default=str)),
            )
        conn.commit()
    return g.number_of_nodes(), g.number_of_edges()


def load_graph() -> nx.DiGraph:
    """Reconstruct a networkx graph from the persisted tables."""
    g: nx.DiGraph = nx.DiGraph()
    with connect() as conn:
        for nid, ntype, name, attrs in conn.execute(
            "SELECT node_id, node_type, name, attrs FROM graph_nodes"
        ).fetchall():
            data = {"node_type": ntype, "name": name}
            if attrs:
                data.update(json.loads(attrs))
            g.add_node(nid, **data)
        for src, tgt, relation, attrs in conn.execute(
            "SELECT src, tgt, relation, attrs FROM graph_edges"
        ).fetchall():
            data = {"relation": relation}
            if attrs:
                data.update(json.loads(attrs))
            g.add_edge(src, tgt, **data)
    return g


def rebuild_and_persist() -> tuple[int, int]:
    """Convenience: build the graph fresh and save it."""
    return persist_graph(build_graph())


# --- graph queries ---------------------------------------------------------- #
def neighbors_of(node_id: str, relation: str | None = None) -> list[dict]:
    """Return neighbour nodes of ``node_id`` (optionally filtered by relation)."""
    g = load_graph()
    out = []
    for _, tgt, data in g.out_edges(node_id, data=True):
        if relation and data.get("relation") != relation:
            continue
        out.append({"node_id": tgt, "relation": data.get("relation", ""), **g.nodes[tgt]})
    for src, _, data in g.in_edges(node_id, data=True):
        if relation and data.get("relation") != relation:
            continue
        out.append({"node_id": src, "relation": data.get("relation", ""), **g.nodes[src]})
    return out


def shortest_path(src: str, tgt: str) -> list[str] | None:
    g = load_graph()
    try:
        return nx.shortest_path(g, src, tgt)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None