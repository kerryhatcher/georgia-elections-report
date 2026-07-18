# Report Site (`web/`)

Astro static site for the Georgia Elections Report. Pages are generated
at build time from the JSON that `generator/` writes into `public/data/`
(gitignored). See `docs/decisions/0001-astro-ssg-with-react-islands.md` for
why this is an Astro SSG rather than a SPA.

## Development

Generate the data first (the build reads it from disk):

```bash
cd ../generator && uv run build.py
```

Then:

```bash
npm install
npm run dev        # serves at http://localhost:4321/naacp-report/
```

Note the `/naacp-report/` base path — the dev server mirrors the GitHub Pages
project-page URL. Internal links must use the `href()` helper in
`src/lib/url.ts`, which prefixes the configured base.

## Scripts

| Script            | What it does                              |
| ----------------- | ----------------------------------------- |
| `npm run dev`     | Dev server with live reload               |
| `npm run build`   | Static build to `dist/`                   |
| `npm run preview` | Serve the production build locally        |
| `npm run check`   | Astro/TypeScript typecheck                |
| `npm test`        | Vitest unit tests (`src/tests/`)          |

## Structure

- `src/lib/data.ts` — reads `public/data/*.json` at build time; the only
  place that touches the generator's output contract.
- `src/pages/counties/[slug].astro` — one static page per county via
  `getStaticPaths`.
- `src/layouts/Layout.astro` — shared head/nav/`<main>`; takes a `title` prop.
- React islands (maps/charts) are supported via `@astrojs/react` but none
  exist yet — turnout and demographics are placeholder pages.

## Deployment

`.github/workflows/deploy.yml` runs tests, builds data + site, and deploys to
GitHub Pages on push to `main`. Hosted at
`https://kerryhatcher.github.io/naacp-report/` (`site` + `base` in
`astro.config.mjs`). If a custom domain is added later, change those two
values and nothing else.

`body_html` is sanitized once, at generation time, with `nh3` — the report
renders it via `set:html` without re-sanitizing (ADR 0001).
