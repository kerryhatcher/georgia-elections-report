# generator

A `uv`-managed Python pipeline that compiles report content/data into static
JSON consumed by the `web/` React app. This is the source of truth for the
report's content — the SPA never talks to a live backend, only to the JSON
this pipeline produces.

## Setup and run

Dependencies are managed with `uv`. From inside `generator/`:

```sh
uv run build.py
```

Output lands in `web/public/data/` (a git-ignored build artifact):

- `counties.json` — lean list (`slug`, `name`, `members`, `selection_method`)
- `counties/<slug>.json` — full detail per county (adds `meeting_schedule`,
  `body_html`)
- `turnout.json`, `demographics.json` — currently empty lists (see below)

## Adding a county

Drop a Markdown file with YAML frontmatter into
`generator/content/county-boards/<slug>.md`. Frontmatter keys:

- `county` — display name
- `members` — number of board members
- `selection_method` — how members are selected
- `meeting_schedule` — when the board meets

The body is Markdown and becomes `body_html`. It's rendered with `markdown`
and sanitized with `nh3` before being written to JSON, so it's safe to embed
directly via `dangerouslySetInnerHTML` on the frontend.

Re-run `uv run build.py` to regenerate the JSON.

## Filling in the stub builders

`turnout.py` and `demographics.py` currently write `[]` — no data has been
collected for those yet. When real data is ready, implement their `build()`
following the `county_boards` pattern (same signature, same `output_dir`
convention). No orchestrator change is needed; `build.py` already calls all
three builders.

## Tests and lint

```sh
uv run pytest
uv run ruff check .
```
