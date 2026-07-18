"""Full-text search across counties, boards, and members.

Powered by SQLite FTS5 with the ``porter unicode61`` tokenizer, so it matches
case-insensitively, stems words (``appoints`` → ``appoint``), and handles
accented characters. Results carry the entity type + id so callers can fetch
the full record.
"""

from __future__ import annotations

from .db import connect
from .models import SearchResult


def search(query: str, limit: int = 20) -> list[SearchResult]:
    """Run an FTS5 MATCH query; returns ranked hits with highlighted snippets."""
    # Build the snippet separately so it isn't escaped into the MATCH string.
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT entity_type, entity_id, title,
                   snippet(search_fts, 3, '→', '←', '…', 12) AS snippet,
                   bm25(search_fts) AS rank
            FROM search_fts
            WHERE search_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
    return [
        SearchResult(
            entity_type=r["entity_type"],
            entity_id=r["entity_id"],
            title=r["title"],
            snippet=r["snippet"],
        )
        for r in rows
    ]


def reindex_all() -> int:
    """Rebuild the FTS index from scratch. Returns the number of rows indexed."""
    from .repo import _index_board, _index_member, list_boards, list_counties, list_members

    with connect() as conn:
        conn.execute("DELETE FROM search_fts")
        conn.commit()

    n = 0
    for c in list_counties():
        from .repo import _index

        _index("county", c.id, c.name, " ".join(filter(None, [c.name, c.seat, str(c.population or "")])))
        n += 1
    for b in list_boards():
        _index_board(b)
        n += 1
    for m in list_members():
        _index_member(m)
        n += 1
    return n