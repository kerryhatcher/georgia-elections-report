# web

The React (Vite + TypeScript + Tailwind + React Router + TanStack Query) SPA
that renders the report from static JSON produced by [`generator/`](../generator/README.md).

## Dev workflow

1. Regenerate the data the app reads:
   ```sh
   cd ../generator && uv run build.py
   ```
2. Install dependencies (first time only):
   ```sh
   npm install
   ```
3. Start the dev server:
   ```sh
   npm run dev
   ```

`public/data/` is a build artifact produced by the generator — it's
git-ignored, not hand-authored. The app fetches its contents at runtime
(`src/lib/api.ts`) as if it were a REST API, but it's really just static
JSON files.

## Build

```sh
npm run build
```

## Pre-deploy checklist (hosting-URL dependent)

These three items are **not** wired up yet because they depend on the final
GitHub Pages URL. Once that URL is chosen, all three MUST change together —
doing only one will break routing or asset loading:

1. **Set Vite `base`** in `vite.config.ts` (e.g. `/naacp-report/` for a
   project page).
2. **Add an SPA deep-link fallback** — a `404.html` copy of `index.html`
   (or switch to `HashRouter` / set a router `basename`) — so routes like
   `/counties/fulton` work on direct load instead of 404ing.
3. **Update `src/lib/api.ts`** — it currently fetches *absolute* paths
   (`/data/...`), which 404 under a project subpath. Make them base-relative
   at the same time, e.g. `` `${import.meta.env.BASE_URL}data/counties.json` ``.
