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

The deploy workflow (`.github/workflows/deploy.yml`) is set to **manual trigger
only** (`workflow_dispatch`) so merging to `main` doesn't auto-publish a site
before hosting is configured. Once the final GitHub Pages URL is chosen, wire up
the items below, then switch the workflow trigger back to `push: branches: [main]`.

1. **Set Vite `base`** in `vite.config.ts` (e.g. `/naacp-report/` for a
   project page). Use an *absolute* base like `/naacp-report/`, not a relative
   `./` — a relative base breaks asset/data resolution on nested BrowserRouter
   routes such as `/counties/fulton`.
2. **Add an SPA deep-link fallback** — a `404.html` copy of `index.html`
   (or switch to `HashRouter` / set a router `basename`) — so routes like
   `/counties/fulton` work on direct load instead of 404ing.
3. ~~**Update `src/lib/api.ts`** to fetch base-relative paths.~~ ✅ **Done** —
   `getJson` now prepends `import.meta.env.BASE_URL`, so fetches automatically
   honor whatever Vite `base` is set in step 1, with no further code change.
