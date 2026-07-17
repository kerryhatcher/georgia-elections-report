# ADR 0001: Pivot the report site from client-rendered React SPA to Astro SSG with React islands

**Date:** 2026-07-17
**Status:** Accepted
**Context:** PR 1 review, item 1 (see `docs/reports/2026-07-17-pr1-review.md`)

## Context

PR 1 shipped the report site as a client-rendered React SPA (Vite + React Router + TanStack Query) on GitHub Pages. Review found this misaligned with the project's mission as a public civic report:

- Deep links (`/counties/fulton`) on GitHub Pages require a `404.html` shim that still serves an **HTTP 404 status code** — search engines won't index those pages and social-preview scrapers break.
- The site ships an empty HTML shell; content appears only after ~95KB gzipped JS boots and fetches JSON. Crawlers and cheap/old phones both suffer.
- Per-page titles/meta/OG tags have no natural home.

All routes are known at build time (159 county slugs + section pages) and all data is static generator output — a textbook static-site-generation case. The pivot is cheapest now, with only 2 real routes wired.

## Constraints (from project owner)

1. **Python stays** as the layer that parses and analyzes raw data and hands off to whatever generates the report.
2. Must work on static hosting (GitHub Pages).
3. Smooth modern UX including **maps, charts, and graphics**.

## Decision

Adopt **Astro** as the report-site framework, consuming the Python generator's JSON at build time via `getStaticPaths()`, with **React islands** for interactive components (MapLibre/Leaflet county maps from pipeline-emitted GeoJSON, Recharts/Plot charts for turnout and demographics).

**Sequencing:** merge PR 1 as-is, then do the Astro pivot as the immediate next PR.

Alternatives considered:
- **Vike prerendering** (stay pure React+Vite): satisfies all constraints; rejected as a less natural fit for a content-heavy report and a smaller ecosystem.
- **Post-build prerender crawl** (react-snap style): fragile on React 19, slow at 159 pages, owns a custom crawler; rejected.
- **Keep SPA + 404.html shim**: least work, but leaves the 404-status/SEO/preview problems unfixed; rejected.

## Consequences

- **Unchanged:** the Python generator, the JSON handoff contract, the content workflow (`.md` → PR → CI → Pages), nh3 build-time sanitization, and most of `deploy.yml`.
- **Deleted, not ported:** React Router, TanStack Query, DOMPurify (build-time consumption makes nh3 the single authoritative sanitization boundary), the `404.html` shim, and the Vite base-path checklist — every route becomes a real HTML file.
- **Ported:** the five small React components' worth of JSX (~1 day at current size).
- Interactive components remain React (Astro mounts them natively), so react-leaflet/Recharts knowledge and ecosystem carry over; each page ships only the JS its islands need.
- The JSON contract becomes load-bearing at build time, strengthening the case for the pydantic contract model (review recommendation #2) landing before or with the pivot.
