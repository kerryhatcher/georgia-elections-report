import { useEffect, useMemo, useRef, useState } from 'react'

/**
 * Interactive county map of Georgia.
 *
 * The SVG path strings for all 159 counties are precomputed at build time
 * (see scripts/build-map-paths.mjs) and served as a small static JSON file,
 * so this island ships no geo library — it just renders <path d=…> and wires
 * up hover/click against the report's county data.
 *
 * Props:
 *  - counties: the report's county summaries (the 9 profiled so far). A
 *    county is "profiled" if its slug appears here.
 *  - base:     the site base path (e.g. "/georgia-elections-report"), used to
 *              build county-page links and to fetch the paths JSON.
 */
export interface CountySummary {
  slug: string
  name: string
  members: number | null
  selection_method: string | null
}

interface CountyPath {
  name: string
  slug: string
  d: string
}

interface PathsFile {
  width: number
  height: number
  counties: CountyPath[]
}

interface Props {
  counties: CountySummary[]
  base: string
}

const trim = (s: string) => s.replace(/\/+$/, '')

export default function CountyMap({ counties, base }: Props) {
  const [paths, setPaths] = useState<PathsFile | null>(null)
  const [hovered, setHovered] = useState<string | null>(null)
  const [mouse, setMouse] = useState<{ x: number; y: number } | null>(null)
  const svgRef = useRef<SVGSVGElement>(null)

  const baseClean = trim(base)

  useEffect(() => {
    let alive = true
    fetch(`${baseClean}/geo/ga-counties-paths.json`)
      .then((r) => r.json())
      .then((data: PathsFile) => {
        if (alive) setPaths(data)
      })
      .catch(() => {
        /* network/preview failure leaves the empty state */
      })
    return () => {
      alive = false
    }
  }, [baseClean])

  // Index the profiled counties by slug for O(1) lookup.
  const profiled = useMemo(() => {
    const map = new Map<string, CountySummary>()
    for (const c of counties) map.set(c.slug, c)
    return map
  }, [counties])

  const profiledCount = profiled.size
  const countyLink = (slug: string) => `${baseClean}/counties/${slug}`

  return (
    <div className="county-map">
      <div className="county-map__legend">
        <span className="county-map__swatch county-map__swatch--profiled" />
        <span className="kicker text-ink-2">Profiled ({profiledCount})</span>
        <span className="county-map__swatch county-map__swatch--pending" />
        <span className="kicker text-ink-2">
          Not yet profiled ({159 - profiledCount})
        </span>
      </div>

      {!paths ? (
        <p className="kicker text-ink-2 county-map__loading">Loading map…</p>
      ) : (
        <svg
          ref={svgRef}
          viewBox={`0 0 ${paths.width} ${paths.height}`}
          className="county-map__svg"
          role="img"
          aria-label="Map of Georgia counties. Counties with a profile are highlighted."
          onMouseLeave={() => {
            setHovered(null)
            setMouse(null)
          }}
        >
          {paths.counties.map((c) => {
            const p = profiled.get(c.slug)
            const isProfiled = Boolean(p)
            const isHovered = hovered === c.slug
            const fill = isProfiled
              ? 'var(--color-accent)'
              : 'var(--color-paper-2)'
            const stroke = isHovered
              ? 'var(--color-ink)'
              : 'var(--color-rule-strong)'
            const strokeWidth = isHovered ? 1.4 : 0.5
            const interactive = isProfiled
            return (
              <path
                key={c.slug}
                d={c.d}
                fill={fill}
                stroke={stroke}
                strokeWidth={strokeWidth}
                style={{
                  cursor: interactive ? 'pointer' : 'default',
                  opacity: isHovered ? 1 : isProfiled ? 0.92 : 1,
                  transition: 'opacity 0.12s, stroke-width 0.12s',
                }}
                onMouseEnter={(e) => {
                  setHovered(c.slug)
                  setMouse({ x: e.clientX, y: e.clientY })
                }}
                onMouseMove={(e) => setMouse({ x: e.clientX, y: e.clientY })}
                onClick={() =>
                  interactive &&
                  (window.location.href = countyLink(c.slug))
                }
                tabIndex={interactive ? 0 : undefined}
                onKeyDown={(e) => {
                  if (interactive && (e.key === 'Enter' || e.key === ' ')) {
                    e.preventDefault()
                    window.location.href = countyLink(c.slug)
                  }
                }}
              >
                <title>
                  {c.name}
                  {isProfiled ? ' — profiled' : ' — not yet profiled'}
                </title>
              </path>
            )
          })}
        </svg>
      )}

      {/* Floating tooltip follows the cursor */}
      {hovered && mouse && (() => {
        const c = paths?.counties.find((x) => x.slug === hovered)
        const p = profiled.get(hovered)
        if (!c) return null
        return (
          <div
            className="county-map__tooltip"
            style={{ left: mouse.x + 14, top: mouse.y + 14 }}
            role="status"
          >
            <p className="county-map__tooltip-name">{c.name} County</p>
            {p ? (
              <p className="county-map__tooltip-meta">
                {p.members ? `${p.members} members · ` : ''}
                <span className="capitalize">{p.selection_method ?? '—'}</span>
                <span className="county-map__tooltip-go"> View profile →</span>
              </p>
            ) : (
              <p className="county-map__tooltip-meta county-map__tooltip-meta--pending">
                Not yet profiled
              </p>
            )}
          </div>
        )
      })()}
    </div>
  )
}