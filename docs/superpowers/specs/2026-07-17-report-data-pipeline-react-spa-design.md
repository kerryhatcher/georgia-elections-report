# Design: Report Data Pipeline + React SPA

Date: 2026-07-17
Status: Approved

## Purpose

The report has three deliverables (see `README.md`): a Georgia county boards of elections directory, county-level turnout rates, and registered voter demographics. This design covers the tooling that will turn researched/collected data into a browsable web report: a Python data pipeline that compiles source content into static JSON, and a React single-page app (SPA) that renders it.

None of the three deliverables have real data collected yet. v1 proves the pipeline end-to-end with one deliverable (county boards) and leaves the other two stubbed, ready to fill in as research completes.

## Architecture

Two independent projects in one repo, connected by a JSON handoff:

```
georgia-elections-report/
  generator/                 # uv-managed Python project
    pyproject.toml
    build.py                 # uv run build.py — orchestrates all collections
    collections/
      county_boards.py
      turnout.py              # stub in v1 — no data yet
      demographics.py         # stub in v1 — no data yet
    content/
      county-boards/
        fulton.md             # Markdown + YAML frontmatter, one file per county
    data/
      turnout/                # CSVs land here once collected
      demographics/
  web/                        # React + Vite + TypeScript app
    src/
      routes/
      components/
    public/
      data/                   # generator writes JSON here — build output, git-ignored
  docs/research/
  sensitive-data/
```

**Data flow:** `uv run build.py` (in `generator/`) reads `content/` and `data/`, and writes JSON directly into `web/public/data/`. Vite serves that folder as static files. In dev, React's `fetch('/data/counties.json')` hits the file Vite is already serving from `public/`. In production, the same static JSON is bundled alongside the built SPA and deployed together — there is no live backend. The JSON files are structured to look like REST API responses so the frontend code reads naturally, but they are pre-computed, not served dynamically.

There is no coupling between the two projects beyond this file handoff: the Python side has no knowledge of React, and the React side has no knowledge of how the JSON was produced, only its shape (see JSON Contract below).

## Python generator internals

`generator/` is a `uv`-managed project (`uv init`-style layout, `uv run` for all commands).

**Collection pattern.** Each content type is a small, independent module in `collections/` exposing one function:

```python
def build() -> None:
    """Reads this collection's content/data sources and writes its JSON output."""
```

`build.py` imports and calls each collection's `build()` in turn. This is the only orchestration logic — there is no shared framework, DAG, or plugin registry. A collection is free to organize its own internals however suits its data; the only contract is the `build()` entry point and where it writes its output.

v1 ships one fully-implemented collection and two stubs:

- **`county_boards.py`** (implemented): reads every `content/county-boards/*.md` file (Markdown body + YAML frontmatter for `title`, `county`, `members`, `selection_method`, `meeting_schedule`, etc., parsed via `python-frontmatter`), renders the Markdown body to HTML, and writes:
  - `web/public/data/counties.json` — a list of lightweight summaries (one per county)
  - `web/public/data/counties/<slug>.json` — one detail file per county, including the rendered HTML body
- **`turnout.py`** (stub): `build()` exists and is called by `build.py`, but does nothing yet (or writes an empty `web/public/data/turnout.json`). No CSV parsing logic until turnout data is collected.
- **`demographics.py`** (stub): same treatment as `turnout.py`.

Adding real turnout/demographics support later means filling in these two modules — `build.py` and `county_boards.py` do not need to change.

## JSON contract

Every collection follows the same list + detail shape, so the frontend's data-fetching code is uniform regardless of deliverable:

```json
// web/public/data/counties.json
[
  { "slug": "fulton", "name": "Fulton", "members": 5, "selection_method": "appointed" }
]
```

```json
// web/public/data/counties/fulton.json
{
  "slug": "fulton",
  "name": "Fulton",
  "members": 5,
  "selection_method": "appointed",
  "meeting_schedule": "First Tuesday monthly",
  "body_html": "<p>The Fulton County Board of Elections...</p>"
}
```

List endpoints stay lean (enough for table/index views); detail endpoints carry the full record, including any rendered Markdown body. Future collections (`turnout.json`, `demographics.json`) will follow the same list/detail split once their data and required fields are known — the exact fields are intentionally not specified yet, since no real data has been collected.

## React app

Stack: Vite + React + TypeScript + React Router + TanStack Query + Tailwind CSS.

- **Routing** (React Router): v1 wires two routes end-to-end —
  - `/counties` — table of all counties, from `counties.json`
  - `/counties/:slug` — single county detail, from `counties/<slug>.json`

  `/turnout` and `/demographics` exist as route placeholders ("data coming soon") so the navigation structure reflects all three deliverables without pretending there's real content behind two of them yet.

- **Data fetching** (TanStack Query): each route's data hook wraps a `fetch()` of the corresponding static JSON file in `useQuery`, giving consistent loading/error states across pages and caching between navigations, even though the underlying data is static per build.

- **Styling** (Tailwind CSS): utility classes throughout; no component library layered on top in v1.

- Out of scope for v1: GIS/map visualization of county boundaries (the GIS boundary sources found in `docs/research/` are for a later deliverable, not this pipeline), authentication, search, and any styling polish beyond a functional Tailwind pass.

## Dev workflow

Two independent toolchains, run separately during development:

- `generator/`: `uv run build.py` regenerates all JSON under `web/public/data/`. Re-run after editing content.
- `web/`: `npm run dev` starts the Vite dev server, which serves `public/data/*.json` as-is.

There is no file-watcher wiring the two together in v1 — regenerating JSON is a manual `uv run build.py` step during content editing.

## Testing

- **Python**: `uv run pytest` in `generator/`. At minimum, one test per implemented collection verifying that a sample content file produces the expected JSON shape (e.g. a fixture `fulton.md` → expected `counties/fulton.json` fields). Stub collections (`turnout`, `demographics`) don't need tests until they have real logic.
- **React**: no test framework configured in v1.

## Deployment

GitHub Actions workflow, triggered on push to `main`:

1. `uv run build.py` in `generator/` — regenerates `web/public/data/`.
2. `npm run build` in `web/` — Vite bundles the SPA into `web/dist/`, copying `public/data/*.json` along with it.
3. Publish `web/dist/` to the `gh-pages` branch (e.g. via `peaceiris/actions-gh-pages` or `actions/deploy-pages`).

Resulting URL: `https://<org>.github.io/georgia-elections-report/`.

## Out of scope / future work

- Turnout and demographics collections (data not yet collected — see README's Data Sources section).
- Any GIS/map rendering of county boundaries.
- CI test running (this design covers local test commands; wiring them into GitHub Actions is a follow-up).
- Search, filtering UI beyond what TanStack Query's caching provides for free.
- Styling beyond a plain Tailwind pass — no design system or branding work yet.
