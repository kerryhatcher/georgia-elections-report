"""CRUD repository for counties, boards, and members.

Each write keeps the ``search_fts`` full-text index in sync, so the data is
always searchable the moment it is written. Graph persistence lives in
``graph.py``; this module owns the relational tables only.
"""

from __future__ import annotations

from .db import connect, init_db
from .models import (
    Board,
    BoardUpdate,
    County,
    CountyUpdate,
    Member,
    MemberUpdate,
)


# --------------------------------------------------------------------------- #
# FTS index helpers
# --------------------------------------------------------------------------- #
def _index(entity_type: str, entity_id: int, title: str, body: str) -> None:
    """Replace the FTS row for one entity (delete-then-insert)."""
    with connect() as conn:
        conn.execute(
            "DELETE FROM search_fts WHERE entity_type = ? AND entity_id = ?",
            (entity_type, entity_id),
        )
        conn.execute(
            "INSERT INTO search_fts (entity_type, entity_id, title, body) "
            "VALUES (?, ?, ?, ?)",
            (entity_type, entity_id, title, body),
        )
        conn.commit()


def _unindex(entity_type: str, entity_id: int) -> None:
    with connect() as conn:
        conn.execute(
            "DELETE FROM search_fts WHERE entity_type = ? AND entity_id = ?",
            (entity_type, entity_id),
        )
        conn.commit()


# --------------------------------------------------------------------------- #
# Counties
# --------------------------------------------------------------------------- #
def create_county(c: County) -> County:
    init_db()
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO counties (name, slug, fips, seat, population)
               VALUES (?, ?, ?, ?, ?)""",
            (c.name, c.slug, c.fips, c.seat, c.population),
        )
        c.id = cur.lastrowid
        conn.commit()
    _index("county", c.id, c.name, " ".join(filter(None, [c.name, c.seat, str(c.population or "")])))
    return c


def get_county(county_id: int) -> County | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM counties WHERE id = ?", (county_id,)).fetchone()
    return County(**dict(row)) if row else None


def get_county_by_slug(slug: str) -> County | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM counties WHERE slug = ?", (slug,)).fetchone()
    return County(**dict(row)) if row else None


def list_counties() -> list[County]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM counties ORDER BY name").fetchall()
    return [County(**dict(r)) for r in rows]


def update_county(county_id: int, upd: CountyUpdate) -> County | None:
    fields = upd.model_dump(exclude_none=True)
    if not fields:
        return get_county(county_id)
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    params = [*fields.values(), county_id]
    with connect() as conn:
        conn.execute(
            f"UPDATE counties SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            params,
        )
        conn.commit()
    county = get_county(county_id)
    if county:
        _index("county", county.id, county.name, " ".join(filter(None, [county.name, county.seat, str(county.population or "")])))
    return county


def delete_county(county_id: int) -> bool:
    # Cascades to boards + members; unindex each before they vanish.
    with connect() as conn:
        boards = conn.execute(
            "SELECT id FROM boards WHERE county_id = ?", (county_id,)
        ).fetchall()
        for b in boards:
            members = conn.execute(
                "SELECT id FROM members WHERE board_id = ?", (b["id"],)
            ).fetchall()
            for m in members:
                _unindex("member", m["id"])
            _unindex("board", b["id"])
        cur = conn.execute("DELETE FROM counties WHERE id = ?", (county_id,))
        conn.commit()
        _unindex("county", county_id)
        return cur.rowcount > 0


# --------------------------------------------------------------------------- #
# Boards
# --------------------------------------------------------------------------- #
def create_board(b: Board) -> Board:
    init_db()
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO boards
                 (county_id, name, organization, meeting_schedule, meeting_location,
                  selection_method, selection_description, authority, term_length, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                b.county_id, b.name, b.organization, b.meeting_schedule,
                b.meeting_location, b.selection_method, b.selection_description,
                b.authority, b.term_length, b.notes,
            ),
        )
        b.id = cur.lastrowid
        conn.commit()
    _index_board(b)
    return b


def _index_board(b: Board) -> None:
    body = " ".join(
        filter(
            None,
            [
                b.name, b.organization, b.meeting_schedule, b.meeting_location,
                b.selection_method, b.selection_description, b.authority,
                b.term_length, b.notes,
            ],
        )
    )
    _index("board", b.id, b.name, body)


def get_board(board_id: int) -> Board | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM boards WHERE id = ?", (board_id,)).fetchone()
    return Board(**dict(row)) if row else None


def get_board_by_county(county_id: int) -> Board | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM boards WHERE county_id = ?", (county_id,)).fetchone()
    return Board(**dict(row)) if row else None


def list_boards() -> list[Board]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM boards ORDER BY name").fetchall()
    return [Board(**dict(r)) for r in rows]


def update_board(board_id: int, upd: BoardUpdate) -> Board | None:
    fields = upd.model_dump(exclude_none=True)
    if not fields:
        return get_board(board_id)
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    params = [*fields.values(), board_id]
    with connect() as conn:
        conn.execute(
            f"UPDATE boards SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            params,
        )
        conn.commit()
    b = get_board(board_id)
    if b:
        _index_board(b)
    return b


def delete_board(board_id: int) -> bool:
    with connect() as conn:
        members = conn.execute(
            "SELECT id FROM members WHERE board_id = ?", (board_id,)
        ).fetchall()
        for m in members:
            _unindex("member", m["id"])
        cur = conn.execute("DELETE FROM boards WHERE id = ?", (board_id,))
        conn.commit()
        _unindex("board", board_id)
        return cur.rowcount > 0


# --------------------------------------------------------------------------- #
# Members
# --------------------------------------------------------------------------- #
def create_member(m: Member) -> Member:
    init_db()
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO members
                 (board_id, name, role, party, is_elected, appointed_by,
                  appointment_method, appointment_authority, term_start, term_end, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                m.board_id, m.name, m.role, m.party, int(m.is_elected),
                m.appointed_by, m.appointment_method, m.appointment_authority,
                m.term_start, m.term_end, m.notes,
            ),
        )
        m.id = cur.lastrowid
        conn.commit()
    _index_member(m)
    return m


def _index_member(m: Member) -> None:
    body = " ".join(
        filter(
            None,
            [
                m.name, m.role, m.party, m.appointed_by, m.appointment_method,
                m.appointment_authority, m.term_start, m.term_end, m.notes,
                "elected" if m.is_elected else "appointed",
            ],
        )
    )
    _index("member", m.id, m.name, body)


def get_member(member_id: int) -> Member | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    return Member(**dict(row)) if row else None


def list_members(board_id: int | None = None) -> list[Member]:
    with connect() as conn:
        if board_id is None:
            rows = conn.execute("SELECT * FROM members ORDER BY name").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM members WHERE board_id = ? ORDER BY name", (board_id,)
            ).fetchall()
    return [Member(**dict(r)) for r in rows]


def update_member(member_id: int, upd: MemberUpdate) -> Member | None:
    fields = upd.model_dump(exclude_none=True)
    if not fields:
        return get_member(member_id)
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    params = [*fields.values(), member_id]
    with connect() as conn:
        conn.execute(
            f"UPDATE members SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            params,
        )
        conn.commit()
    m = get_member(member_id)
    if m:
        _index_member(m)
    return m


def delete_member(member_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
        conn.commit()
        _unindex("member", member_id)
        return cur.rowcount > 0