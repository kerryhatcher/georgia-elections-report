"""Command-line interface for the Georgia board-of-elections database.

Run ``boe --help``. Subcommands mirror the data model:

    boe init                       create the schema
    boe seed                       load county boards from content/county-boards
    boe counties add|list|show|update|delete
    boe boards    add|list|show|update|delete
    boe members   add|list|show|update|delete
    boe search  <query>            full-text search across everything
    boe graph build|show|path|neighbors

Every write keeps the FTS index in sync; ``boe graph build`` persists the
networkx relations graph to the database.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import graph as graph_mod
from . import repo
from .db import db_path, init_db
from .models import Board, BoardUpdate, County, CountyUpdate, Member, MemberUpdate
from .search import reindex_all, search

app = typer.Typer(
    no_args_is_help=True,
    help="Georgia board-of-elections database: CRUD, full-text search, relations graph.",
)
counties_app = typer.Typer(no_args_is_help=True, help="Counties.")
boards_app = typer.Typer(no_args_is_help=True, help="Boards of elections.")
members_app = typer.Typer(no_args_is_help=True, help="Board members (people).")
graph_app = typer.Typer(no_args_is_help=True, help="networkx relations graph.")

app.add_typer(counties_app, name="counties")
app.add_typer(boards_app, name="boards")
app.add_typer(members_app, name="members")
app.add_typer(graph_app, name="graph")

console = Console()


# --------------------------------------------------------------------------- #
# top-level
# --------------------------------------------------------------------------- #
@app.command()
def init() -> None:
    """Create the database schema (idempotent)."""
    init_db()
    typer.echo(f"Database ready at {db_path()}")


@app.command()
def seed() -> None:
    """Load county boards from content/county-boards/*.md frontmatter.

    Idempotent: counties already present (by slug) are skipped. Adds a few
    placeholder members for Bibb so the graph has people to show.
    """
    import frontmatter

    init_db()
    content_dir = Path(__file__).resolve().parents[1] / "content" / "county-boards"
    if not content_dir.exists():
        typer.echo(f"No content dir at {content_dir}", err=True)
        raise typer.Exit(1)

    added_counties = added_boards = 0
    for md_path in sorted(content_dir.glob("*.md")):
        post = frontmatter.load(md_path)
        slug = md_path.stem
        if repo.get_county_by_slug(slug):
            continue
        county = repo.create_county(
            County(name=post.get("county", slug), slug=slug)
        )
        added_counties += 1
        board = repo.create_board(
            Board(
                county_id=county.id,  # type: ignore[arg-type]
                name=post.get("title", f"{post.get('county', slug)} Board of Elections"),
                meeting_schedule=post.get("meeting_schedule"),
                selection_method=post.get("selection_method"),
                organization=post.content.strip().splitlines()[0] if post.content.strip() else None,
            )
        )
        added_boards += 1
        # Placeholder members for the pilot county so the graph is interesting.
        if slug == "bibb":
            for name, role, party, method, by, authority in [
                ("Placeholder A", "chair", "Democratic", "party nomination", "Democratic Party", "Local act"),
                ("Placeholder B", "member", "Republican", "party nomination", "Republican Party", "Local act"),
                ("Placeholder C", "member", "Democratic", "party nomination", "Democratic Party", "Local act"),
                ("Placeholder D", "member", "Republican", "party nomination", "Republican Party", "Local act"),
                ("Placeholder E", "member", None, "mayoral appointment", "Mayor of Macon-Bibb", "Consolidated government charter"),
            ]:
                repo.create_member(
                    Member(
                        board_id=board.id,  # type: ignore[arg-type]
                        name=name, role=role, party=party,
                        is_elected=False, appointment_method=method,
                        appointed_by=by, appointment_authority=authority,
                        notes="Placeholder — replace with verified data.",
                    )
                )

    typer.echo(
        f"Seeded {added_counties} counties and {added_boards} boards "
        f"(skipped {len(list(content_dir.glob('*.md'))) - added_counties} existing)."
    )


@app.command()
def reindex() -> None:
    """Rebuild the full-text search index from scratch."""
    n = reindex_all()
    typer.echo(f"Reindexed {n} rows.")


@app.command()
def search_cmd(
    query: str = typer.Argument(..., help="FTS5 MATCH expression, e.g. 'appointed'"),
    limit: int = typer.Option(20, "--limit", "-n"),
) -> None:
    """Full-text search across counties, boards, and members."""
    hits = search(query, limit=limit)
    if not hits:
        typer.echo("No matches.")
        return
    table = Table("Type", "ID", "Title", "Snippet")
    for h in hits:
        table.add_row(h.entity_type, str(h.entity_id), h.title, h.snippet)
    console.print(table)


# --------------------------------------------------------------------------- #
# counties
# --------------------------------------------------------------------------- #
@counties_app.command("add")
def counties_add(
    name: str = typer.Option(..., "--name"),
    slug: str = typer.Option(..., "--slug"),
    fips: str | None = typer.Option(None, "--fips"),
    seat: str | None = typer.Option(None, "--seat"),
    population: int | None = typer.Option(None, "--population"),
) -> None:
    c = repo.create_county(County(name=name, slug=slug, fips=fips, seat=seat, population=population))
    typer.echo(f"Created county #{c.id}: {c.name} ({c.slug})")


@counties_app.command("list")
def counties_list() -> None:
    rows = repo.list_counties()
    table = Table("ID", "Slug", "Name", "FIPS", "Seat", "Pop.")
    for c in rows:
        table.add_row(str(c.id), c.slug, c.name, c.fips or "—", c.seat or "—", str(c.population or "—"))
    console.print(table)


@counties_app.command("show")
def counties_show(county_id: int = typer.Argument(...)) -> None:
    c = repo.get_county(county_id)
    if not c:
        typer.echo("Not found.", err=True)
        raise typer.Exit(1)
    for k, v in c.model_dump().items():
        typer.echo(f"{k:>12}: {v}")


@counties_app.command("update")
def counties_update(
    county_id: int = typer.Argument(...),
    name: str | None = typer.Option(None),
    slug: str | None = typer.Option(None),
    fips: str | None = typer.Option(None),
    seat: str | None = typer.Option(None),
    population: int | None = typer.Option(None),
) -> None:
    c = repo.update_county(county_id, CountyUpdate(name=name, slug=slug, fips=fips, seat=seat, population=population))
    typer.echo(f"Updated county #{c.id}" if c else "Not found.")


@counties_app.command("delete")
def counties_delete(county_id: int = typer.Argument(...)) -> None:
    typer.echo("Deleted." if repo.delete_county(county_id) else "Not found.")


# --------------------------------------------------------------------------- #
# boards
# --------------------------------------------------------------------------- #
@boards_app.command("add")
def boards_add(
    county_id: int = typer.Option(..., "--county-id"),
    name: str = typer.Option(..., "--name"),
    organization: str | None = typer.Option(None),
    meeting_schedule: str | None = typer.Option(None, "--meeting-schedule"),
    meeting_location: str | None = typer.Option(None, "--meeting-location"),
    selection_method: str | None = typer.Option(None, "--selection-method"),
    selection_description: str | None = typer.Option(None, "--selection-description"),
    authority: str | None = typer.Option(None),
    term_length: str | None = typer.Option(None, "--term-length"),
    notes: str | None = typer.Option(None),
) -> None:
    b = repo.create_board(
        Board(
            county_id=county_id, name=name, organization=organization,
            meeting_schedule=meeting_schedule, meeting_location=meeting_location,
            selection_method=selection_method, selection_description=selection_description,
            authority=authority, term_length=term_length, notes=notes,
        )
    )
    typer.echo(f"Created board #{b.id}: {b.name}")


@boards_app.command("list")
def boards_list() -> None:
    table = Table("ID", "County", "Name", "Method", "Meets")
    for b in repo.list_boards():
        c = repo.get_county(b.county_id)
        table.add_row(str(b.id), c.slug if c else "—", b.name, b.selection_method or "—", b.meeting_schedule or "—")
    console.print(table)


@boards_app.command("show")
def boards_show(board_id: int = typer.Argument(...)) -> None:
    b = repo.get_board(board_id)
    if not b:
        typer.echo("Not found.", err=True)
        raise typer.Exit(1)
    for k, v in b.model_dump().items():
        typer.echo(f"{k:>22}: {v}")


@boards_app.command("update")
def boards_update(
    board_id: int = typer.Argument(...),
    name: str | None = typer.Option(None),
    organization: str | None = typer.Option(None),
    meeting_schedule: str | None = typer.Option(None, "--meeting-schedule"),
    meeting_location: str | None = typer.Option(None, "--meeting-location"),
    selection_method: str | None = typer.Option(None, "--selection-method"),
    selection_description: str | None = typer.Option(None, "--selection-description"),
    authority: str | None = typer.Option(None),
    term_length: str | None = typer.Option(None, "--term-length"),
    notes: str | None = typer.Option(None),
) -> None:
    b = repo.update_board(
        board_id,
        BoardUpdate(name=name, organization=organization, meeting_schedule=meeting_schedule,
                    meeting_location=meeting_location, selection_method=selection_method,
                    selection_description=selection_description, authority=authority,
                    term_length=term_length, notes=notes),
    )
    typer.echo(f"Updated board #{b.id}" if b else "Not found.")


@boards_app.command("delete")
def boards_delete(board_id: int = typer.Argument(...)) -> None:
    typer.echo("Deleted." if repo.delete_board(board_id) else "Not found.")


# --------------------------------------------------------------------------- #
# members
# --------------------------------------------------------------------------- #
@members_app.command("add")
def members_add(
    board_id: int = typer.Option(..., "--board-id"),
    name: str = typer.Option(..., "--name"),
    role: str | None = typer.Option(None),
    party: str | None = typer.Option(None),
    is_elected: bool = typer.Option(False, "--is-elected/--not-elected"),
    appointed_by: str | None = typer.Option(None, "--appointed-by"),
    appointment_method: str | None = typer.Option(None, "--appointment-method"),
    appointment_authority: str | None = typer.Option(None, "--appointment-authority"),
    term_start: str | None = typer.Option(None, "--term-start"),
    term_end: str | None = typer.Option(None, "--term-end"),
    notes: str | None = typer.Option(None),
) -> None:
    m = repo.create_member(
        Member(board_id=board_id, name=name, role=role, party=party, is_elected=is_elected,
               appointed_by=appointed_by, appointment_method=appointment_method,
               appointment_authority=appointment_authority, term_start=term_start,
               term_end=term_end, notes=notes)
    )
    typer.echo(f"Created member #{m.id}: {m.name}")


@members_app.command("list")
def members_list(board_id: int | None = typer.Option(None, "--board-id")) -> None:
    table = Table("ID", "Board", "Name", "Role", "Party", "Elected", "Appointed by")
    for m in repo.list_members(board_id=board_id):
        b = repo.get_board(m.board_id)
        table.add_row(str(m.id), b.name if b else "—", m.name, m.role or "—",
                      m.party or "—", "yes" if m.is_elected else "no", m.appointed_by or "—")
    console.print(table)


@members_app.command("show")
def members_show(member_id: int = typer.Argument(...)) -> None:
    m = repo.get_member(member_id)
    if not m:
        typer.echo("Not found.", err=True)
        raise typer.Exit(1)
    for k, v in m.model_dump().items():
        typer.echo(f"{k:>22}: {v}")


@members_app.command("update")
def members_update(
    member_id: int = typer.Argument(...),
    name: str | None = typer.Option(None),
    role: str | None = typer.Option(None),
    party: str | None = typer.Option(None),
    is_elected: bool | None = typer.Option(None, "--is-elected/--not-elected"),
    appointed_by: str | None = typer.Option(None, "--appointed-by"),
    appointment_method: str | None = typer.Option(None, "--appointment-method"),
    appointment_authority: str | None = typer.Option(None, "--appointment-authority"),
    term_start: str | None = typer.Option(None, "--term-start"),
    term_end: str | None = typer.Option(None, "--term-end"),
    notes: str | None = typer.Option(None),
) -> None:
    m = repo.update_member(
        member_id,
        MemberUpdate(name=name, role=role, party=party, is_elected=is_elected,
                     appointed_by=appointed_by, appointment_method=appointment_method,
                     appointment_authority=appointment_authority, term_start=term_start,
                     term_end=term_end, notes=notes),
    )
    typer.echo(f"Updated member #{m.id}" if m else "Not found.")


@members_app.command("delete")
def members_delete(member_id: int = typer.Argument(...)) -> None:
    typer.echo("Deleted." if repo.delete_member(member_id) else "Not found.")


# --------------------------------------------------------------------------- #
# graph
# --------------------------------------------------------------------------- #
@graph_app.command("build")
def graph_build() -> None:
    """Build the relations graph from the tables and persist it."""
    nodes, edges = graph_mod.rebuild_and_persist()
    typer.echo(f"Persisted graph: {nodes} nodes, {edges} edges.")


@graph_app.command("show")
def graph_show() -> None:
    """Show counts and a sample of the persisted graph."""
    g = graph_mod.load_graph()
    if g.number_of_nodes() == 0:
        typer.echo("Graph is empty. Run `boe graph build` first.")
        return
    typer.echo(f"Nodes: {g.number_of_nodes()}  Edges: {g.number_of_edges()}")
    table = Table("Node", "Type", "Name")
    for nid, data in list(g.nodes(data=True))[:15]:
        table.add_row(nid, str(data.get("node_type")), str(data.get("name")))
    console.print(table)


@graph_app.command("neighbors")
def graph_neighbors(
    node_id: str = typer.Argument(..., help="e.g. board:1 or county:bibb"),
    relation: str | None = typer.Option(None, "--relation"),
) -> None:
    nbrs = graph_mod.neighbors_of(node_id, relation=relation)
    if not nbrs:
        typer.echo("No neighbours (or node not found).")
        return
    table = Table("Node", "Type", "Name", "Relation")
    for n in nbrs:
        table.add_row(n["node_id"], str(n.get("node_type")), str(n.get("name")), str(n.get("relation", "")))
    console.print(table)


@graph_app.command("path")
def graph_path(
    src: str = typer.Argument(...),
    tgt: str = typer.Argument(...),
) -> None:
    p = graph_mod.shortest_path(src, tgt)
    if not p:
        typer.echo("No path found.")
        return
    typer.echo(" → ".join(p))


# expose `search` under its real name (typer mangles `search_cmd`)
search_cmd.__name__ = "search"


if __name__ == "__main__":
    app()