# `boe` — Board of Elections Database

A SQLite-backed store for Georgia's county boards of elections: who sits on
each board, how each board is organized, when/where it meets, and how its
members are chosen — with full-text search and a networkx graph of the
relations among the state, counties, boards, and people.

The database file lives at the **repository root** (`database.db`,
gitignored) so every contributor has a local working copy. Override the path
with the `BOE_DB_PATH` environment variable (handy for tests).

## Quick start

```bash
cd generator
uv sync
uv run boe init              # create the schema
uv run boe seed               # load county boards from content/county-boards/*.md
uv run boe graph build        # build + persist the relations graph
```

## Data model

Pydantic models in `boe/models.py` mirror the SQLite schema in `boe/db.py`:

- **County** — one of Georgia's 159 counties (`name`, `slug`, `fips`, `seat`, `population`).
- **Board** — one per county (1:1). How it is organized (`organization`), when
  and where it meets (`meeting_schedule`, `meeting_location`), and how members
  are chosen: `selection_method` (`appointed` / `elected` / `mixed`),
  `selection_description`, the `authority` (local act / charter) that creates
  it, and `term_length`.
- **Member** — a person on a board: `name`, `role`, `party`, `is_elected`,
  `appointed_by`, `appointment_method`, `appointment_authority`, term dates.

## CLI

```
boe init                                          create the schema
boe seed                                          load county boards from content/
boe reindex                                       rebuild the FTS index from scratch

boe counties add   --name --slug [--fips --seat --population]
boe counties list
boe counties show <id>
boe counties update <id> [--name --slug --fips --seat --population]
boe counties delete <id>                         # cascades to boards + members

boe boards add   --county-id --name [--organization --meeting-schedule
                  --meeting-location --selection-method --selection-description
                  --authority --term-length --notes]
boe boards list | show <id> | update <id> [...] | delete <id>

boe members add   --board-id --name [--role --party --is-elected --appointed-by
                  --appointment-method --appointment-authority --term-start
                  --term-end --notes]
boe members list [--board-id] | show <id> | update <id> [...] | delete <id>

boe search <query> [-n LIMIT]                     full-text search across everything
boe graph build                                   build + persist the relations graph
boe graph show                                    node/edge counts + sample nodes
boe graph neighbors <node-id> [--relation R]      e.g. board:1, county:bibb, person:3
boe graph path <src> <tgt>                         shortest path, e.g. state:GA person:1
```

## Full-text search

Every write keeps an **FTS5** index (`search_fts`) in sync, so data is
searchable the moment it is written. The `porter unicode61` tokenizer matches
case-insensitively, stems words (`appoints` → `appoint`), and handles
accented characters. Results carry the entity type + id so you can fetch the
full record.

```bash
uv run boe search "appointed"
uv run boe search "democratic"      # stems to match "Democratic"
uv run boe search "government center"
```

## Relations graph (networkx)

`boe/graph.py` models the election-administration hierarchy as a directed
graph:

```
state:GA ──contains──▶ county:{slug} ──has_board──▶ board:{id} ──has_member──▶ person:{id}
                                          ◀──serves_on──
```

`boe graph build` reconstructs it from the relational tables (source of truth)
and persists it to `graph_nodes` / `graph_edges` (attrs as JSON). The graph is
then queryable without rebuilding it. Node ids: `state:GA`, `county:{slug}`,
`board:{id}`, `person:{id}`.

```bash
uv run boe graph path state:GA person:1
# state:GA → county:bibb → board:1 → person:1
```

## Layout

```
boe/
  __init__.py   re-exports init_db
  models.py     pydantic models (County, Board, Member + Update payloads)
  db.py         SQLite connection + schema (FTS5, graph tables)
  repo.py       CRUD; keeps search_fts in sync on every write
  search.py     FTS5 search + reindex_all
  graph.py      build / persist / load / query the networkx graph
  cli.py        typer CLI (entry point: `boe`)
```

## Tests

```bash
cd generator && uv run python -m pytest
```

`tests/test_boe.py` exercises CRUD, cascade deletes, FTS sync, and the graph
round-trip using a throwaway temp database (`BOE_DB_PATH`).