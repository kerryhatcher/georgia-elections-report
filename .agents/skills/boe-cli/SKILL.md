---
name: boe-cli
description: "Drive the Georgia board-of-elections SQLite database via the `boe` CLI — CRUD for counties, boards, and members; FTS5 full-text search; and the networkx relations graph among the state, counties, boards, and people. Use whenever a task touches county boards of elections, their members, meeting/selection/appointment details, or the state→county→board→person relations graph. The DB lives at the repo-root database.db (gitignored); the CLI lives in generator/."
---

# `boe` — Georgia Board of Elections Database CLI

A SQLite-backed store (package `boe`, in `generator/`) tracking Georgia's 159
county boards of elections, the people on them, how each board is organized,
when/where it meets, and how members are chosen — with full-text search and a
networkx relations graph, all persisted to the gitignored repo-root
`database.db`.

## Ground rules

- **Run from `generator/`:** `cd generator && uv run boe <command>`.
- **The DB is local & gitignored** (`database.db` at repo root). Never commit
  it. For throwaway work, set `BOE_DB_PATH=/tmp/whatever.db` so you don't mutate
  the real one.
- **`init` is idempotent** (`CREATE TABLE IF NOT EXISTS`); it will NOT add
  columns to an existing outdated table. If the schema changed, drop the DB (or
  use a fresh `BOE_DB_PATH`) and re-run `init` + `seed`.
- **Search sync is automatic** on every write. **Graph sync is manual** — re-run
  `boe graph build` after data changes if you want the persisted graph current.
- **Cascade deletes:** `counties delete <id>` removes the county's board, that
  board's members, and all their search rows. `boards delete <id>` removes the
  board's members + search rows.

## First-run setup

```bash
cd generator
uv sync
uv run boe init              # create the SQLite schema (idempotent)
uv run boe seed               # load county boards from content/county-boards/*.md (idempotent; adds placeholder Bibb members)
uv run boe graph build        # build + persist the relations graph
```

`seed` skips counties already present (matched by slug). The placeholder
members it adds for Bibb are clearly marked — replace with verified data via
`boe members update`.

## Data model (pydantic, `generator/boe/models.py`)

- **County** — `name`, `slug` (unique), `fips`, `seat`, `population`.
- **Board** — 1:1 with a county. `organization`, `meeting_schedule`,
  `meeting_location`, `selection_method` (`appointed` | `elected` | `mixed`),
  `selection_description` (how/by whom chosen), `authority` (local act/charter),
  `term_length`, `notes`.
- **Member** — a person on a board: `name`, `role`, `party`, `is_elected`,
  `appointed_by`, `appointment_method`, `appointment_authority`, `term_start`,
  `term_end`, `notes`.

## CRUD

```bash
# Counties
uv run boe counties add   --name Bibb --slug bibb [--fips 13021 --seat Macon --population 157000]
uv run boe counties list
uv run boe counties show <id>
uv run boe counties update <id> [--name ... --seat ... --population ...]
uv run boe counties delete <id>          # cascades to board + members

# Boards  (note: --county-id, not --county)
uv run boe boards add   --county-id 1 --name "Macon-Bibb County Board of Elections" \
    [--organization "..." --meeting-schedule "Third Thursday monthly, 12:00 PM" \
     --meeting-location "..." --selection-method appointed \
     --selection-description "Two named by each major party, fifth by the mayor." \
     --authority "Consolidated government charter" --term-length "4 years" --notes "..."]
uv run boe boards list | show <id> | update <id> [...] | delete <id>

# Members  (note: --board-id, not --board)
uv run boe members add   --board-id 1 --name "Jane Doe" \
    [--role chair --party Democratic --is-elected/--not-elected \
     --appointed-by "Democratic Party" --appointment-method "party nomination" \
     --appointment-authority "Local act" --term-start 2024-01 --term-end 2028-01 --notes "..."]
uv run boe members list [--board-id 1]      # filter to one board, or list all
uv run boe members show <id> | update <id> [...] | delete <id>
```

`update` commands take only the flags you want to change; omitted flags are
left untouched (partial update, not overwrite).

## Full-text search (FTS5)

Automatic on every write. Case-insensitive, stems (`appoints` → `appoint`,
`democrats` → `Democratic`), handles accents. Ranked by `bm25` with snippets.

```bash
uv run boe search "appointed"
uv run boe search "democratic"          # stems → matches "Democratic"
uv run boe search "government center"   # multi-term
uv run boe search "zzznotreal"           # → "No matches."
uv run boe search "macon" -n 5           # -n / --limit caps results
uv run boe reindex                        # rebuild FTS from scratch if it drifts
```

## Relations graph (networkx)

Hierarchy: `state:GA ──contains──▶ county:{slug} ──has_board──▶ board:{id} ──has_member──▶ person:{id}`
with reverse `serves_on` (person → board). Node ids: `state:GA`,
`county:{slug}` (e.g. `county:bibb`), `board:{id}` (e.g. `board:1`),
`person:{id}` (e.g. `person:3`).

```bash
uv run boe graph build                    # rebuild from tables + persist (run after data changes)
uv run boe graph show                      # node/edge counts + sample nodes
uv run boe graph neighbors board:1         # everything adjacent to a board
uv run boe graph neighbors county:bibb --relation has_board   # filter by edge type
uv run boe graph path state:GA person:1    # shortest path: state → county → board → person
```

The graph is a **snapshot** — `build_graph` reconstructs from the relational
tables (source of truth) and `persist_graph` writes to `graph_nodes` /
`graph_edges`. It does not auto-update on CRUD; re-run `boe graph build`.

## Programmatic use (for agents scripting against the DB)

```python
from boe import repo, graph
from boe.models import County, Board, Member
from boe.search import search

repo.create_county(County(name="Bibb", slug="bibb", seat="Macon"))
hits = search("macon")                    # list[SearchResult]
g = graph.build_graph()                    # nx.DiGraph
graph.persist_graph(g)                     # write to DB
g = graph.load_graph()                     # read back
graph.shortest_path("state:GA", "person:1")
```

## Layout

```
generator/boe/
  models.py   pydantic models (County, Board, Member + Update payloads)
  db.py       SQLite connection + schema (FTS5, graph tables)
  repo.py     CRUD; keeps search_fts in sync on every write
  search.py   FTS5 search + reindex_all
  graph.py    build / persist / load / query the networkx graph
  cli.py      typer CLI (entry point: `boe`)
generator/tests/test_boe.py   CRUD + FTS + graph tests (temp DB via BOE_DB_PATH)
```

## Verify your work

```bash
cd generator
uv run ruff check .          # lint must pass
uv run python -m pytest      # 22 tests (16 boe + 6 existing)
uv run build.py              # the report-data build still works
```

Tests use a temp DB via `BOE_DB_PATH`, so running them never touches the real
`database.db`.