"""Tests for the boe package: CRUD, FTS search, and the networkx graph.

Each test uses a throwaway temp database via the ``BOE_DB_PATH`` env var so
nothing touches the real ``database.db`` at the repo root.
"""

from __future__ import annotations


import pytest

from boe import graph, repo
from boe.db import init_db
from boe.models import Board, County, Member
from boe.search import search


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("BOE_DB_PATH", str(db))
    init_db()
    return db


@pytest.fixture()
def seeded(tmp_db):
    """A small seeded dataset: one county, one board, two members."""
    county = repo.create_county(County(name="Bibb", slug="bibb", seat="Macon", population=157000))
    board = repo.create_board(
        Board(
            county_id=county.id,  # type: ignore[arg-type]
            name="Macon-Bibb County Board of Elections",
            meeting_schedule="Third Thursday monthly, 12:00 PM",
            selection_method="appointed",
            selection_description="Two named by each major party, fifth by the mayor.",
        )
    )
    repo.create_member(
        Member(
            board_id=board.id,  # type: ignore[arg-type]
            name="Jane Doe", role="chair", party="Democratic",
            appointed_by="Democratic Party", appointment_method="party nomination",
        )
    )
    repo.create_member(
        Member(
            board_id=board.id,  # type: ignore[arg-type]
            name="John Roe", role="member", party="Republican",
            appointed_by="Republican Party", appointment_method="party nomination",
        )
    )
    return county, board


# --------------------------------------------------------------------------- #
# CRUD
# --------------------------------------------------------------------------- #
def test_create_and_get_county(seeded):
    county, _ = seeded
    assert county.id is not None
    fetched = repo.get_county(county.id)
    assert fetched is not None
    assert fetched.name == "Bibb"
    assert fetched.seat == "Macon"


def test_get_county_by_slug(seeded):
    assert repo.get_county_by_slug("bibb").name == "Bibb"
    assert repo.get_county_by_slug("nope") is None


def test_update_county(seeded):
    county, _ = seeded
    from boe.models import CountyUpdate

    updated = repo.update_county(county.id, CountyUpdate(population=160000))
    assert updated.population == 160000
    # unchanged fields preserved
    assert updated.name == "Bibb"


def test_update_board(seeded):
    _, board = seeded
    from boe.models import BoardUpdate

    updated = repo.update_board(board.id, BoardUpdate(meeting_location="Government Center"))
    assert updated.meeting_location == "Government Center"
    assert updated.name == "Macon-Bibb County Board of Elections"


def test_list_members_filtered_by_board(seeded):
    _, board = seeded
    members = repo.list_members(board_id=board.id)
    assert len(members) == 2
    assert {m.name for m in members} == {"Jane Doe", "John Roe"}


def test_delete_member_unindexes(seeded):
    _, board = seeded
    m = repo.list_members(board_id=board.id)[0]
    assert repo.delete_member(m.id) is True
    assert repo.get_member(m.id) is None
    # the deleted member should not be searchable
    assert not any(h.entity_id == m.id for h in search(m.name))


def test_delete_county_cascades(seeded):
    county, board = seeded
    member_ids = [m.id for m in repo.list_members(board_id=board.id)]
    assert repo.delete_county(county.id) is True
    assert repo.get_county(county.id) is None
    assert repo.get_board(board.id) is None  # cascaded
    for mid in member_ids:
        assert repo.get_member(mid) is None  # cascaded


# --------------------------------------------------------------------------- #
# Full-text search
# --------------------------------------------------------------------------- #
def test_search_finds_county_by_seat(seeded):
    hits = search("Macon")
    types = {h.entity_type for h in hits}
    assert "county" in types
    assert "board" in types  # "Macon-Bibb" board name


def test_search_finds_member_by_name(seeded):
    hits = search("Jane")
    assert any(h.entity_type == "member" and h.title == "Jane Doe" for h in hits)


def test_search_finds_member_by_party_stemming(seeded):
    # "democrats" should stem to match "Democratic"
    hits = search("democrats")
    assert any(h.entity_type == "member" for h in hits)


def test_search_no_results(seeded):
    assert search("zzznotreal") == []


# --------------------------------------------------------------------------- #
# Graph
# --------------------------------------------------------------------------- #
def test_build_and_persist_graph(seeded):
    county, board = seeded
    nodes, edges = graph.rebuild_and_persist()
    # 1 state + 1 county + 1 board + 2 people = 5 nodes
    assert nodes == 5
    # contains + has_board + 2×(has_member+serves_on) = 6 edges
    assert edges == 6


def test_load_graph_roundtrip(seeded):
    graph.rebuild_and_persist()
    g = graph.load_graph()
    assert g.number_of_nodes() == 5
    assert "state:GA" in g
    assert "county:bibb" in g
    assert "board:" + str(repo.get_board_by_county(repo.get_county_by_slug("bibb").id).id) in g


def test_shortest_path_state_to_person(seeded):
    graph.rebuild_and_persist()
    _, board = seeded
    person = repo.list_members(board_id=board.id)[0]
    path = graph.shortest_path("state:GA", f"person:{person.id}")
    assert path is not None
    assert path[0] == "state:GA"
    assert path[-1] == f"person:{person.id}"
    # must traverse county and board on the way
    assert "county:bibb" in path
    assert f"board:{board.id}" in path


def test_neighbors_of_board(seeded):
    graph.rebuild_and_persist()
    _, board = seeded
    nbrs = graph.neighbors_of(f"board:{board.id}")
    relations = {n["relation"] for n in nbrs}
    assert "has_board" in relations   # county -> board
    assert "has_member" in relations  # board -> person


def test_neighbors_filtered_by_relation(seeded):
    graph.rebuild_and_persist()
    _, board = seeded
    nbrs = graph.neighbors_of(f"board:{board.id}", relation="has_member")
    assert all(n["relation"] == "has_member" for n in nbrs)
    assert len(nbrs) == 2