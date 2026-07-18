#!/usr/bin/env node
// Precompute SVG path strings for the 159 Georgia counties from the
// committed TopoJSON boundary file, so the map page needs no geo library
// at runtime — it just renders <path d=…> from a small JSON file.
//
// Input : scripts/data/ga-counties.topojson.json  (committed reference data)
// Output: public/geo/ga-counties-paths.json       (committed; served static)
//
// Run:  node scripts/build-map-paths.mjs

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import * as topojson from 'topojson-client'
import { geoMercator, geoPath } from 'd3-geo'

// Ramer–Douglas–Peucker simplification, applied in lon/lat space. Tolerance is
// in degrees (~0.003° ≈ 330 m): enough to drop the sub-county wiggle that is
// invisible at a 600px-wide report map while keeping every boundary legible.
const dpTolerance = 0.003
function dp(points, eps) {
  if (points.length < 3) return points
  let maxDist = -1
  let idx = 0
  const [ax, ay] = points[0]
  const [bx, by] = points[points.length - 1]
  for (let i = 1; i < points.length - 1; i++) {
    const [px, py] = points[i]
    // Perpendicular distance from point p to line a-b (lon/lat treated as flat).
    const dx = bx - ax
    const dy = by - ay
    const len2 = dx * dx + dy * dy
    let dist = 0
    if (len2 !== 0) {
      const t = ((px - ax) * dx + (py - ay) * dy) / len2
      const cx = ax + t * dx
      const cy = ay + t * dy
      dist = Math.hypot(px - cx, py - cy)
    } else {
      dist = Math.hypot(px - ax, py - ay)
    }
    if (dist > maxDist) {
      maxDist = dist
      idx = i
    }
  }
  if (maxDist > eps) {
    const left = dp(points.slice(0, idx + 1), eps)
    const right = dp(points.slice(idx), eps)
    return left.slice(0, -1).concat(right)
  }
  return [points[0], points[points.length - 1]]
}
function simplifyRing(ring) {
  return dp(ring, dpTolerance)
}
function simplifyCoords(coords, isMulti) {
  // Polygon: coords = [ring, ring, ...]; MultiPolygon: coords = [[ring,...], ...]
  if (isMulti) return coords.map((poly) => poly.map(simplifyRing))
  return coords.map(simplifyRing)
}

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')

const topoPath = path.join(__dirname, 'data', 'ga-counties.topojson.json')
const outDir = path.join(root, 'public', 'geo')
const outPath = path.join(outDir, 'ga-counties-paths.json')

const topo = JSON.parse(readFileSync(topoPath, 'utf-8'))
// The TopoJSON object name in kthotav's file is "georgia-counties".
const fc = topojson.feature(topo, topo.objects['georgia-counties'])

// Fit a Mercator projection to Georgia's extent. A single-state Mercator is
// fine at this latitude range (30–35°N); the slight distortion is invisible at
// report scale.
const W = 600
const H = 360
const pad = 14
const projection = geoMercator().fitExtent(
  [
    [pad, pad],
    [W - pad, H - pad],
  ],
  fc,
)
const pathGen = geoPath(projection)

// Round path coordinates to one decimal place — sub-pixel precision is
// invisible at report scale and shrinks the JSON meaningfully.
const round = (d) =>
  d ? d.replace(/-?\d+\.\d+/g, (m) => Number(m).toFixed(1)) : d

const counties = fc.features.map((f) => {
  const name = f.properties.NAME
  // Simplify before projecting so fewer points flow into the path string.
  const isMulti = f.geometry.type === 'MultiPolygon'
  f.geometry.coordinates = simplifyCoords(f.geometry.coordinates, isMulti)
  return {
    name,
    slug: name.toLowerCase(),
    d: round(pathGen(f) || ''),
  }
})

mkdirSync(outDir, { recursive: true })
const out = { width: W, height: H, counties }
writeFileSync(outPath, JSON.stringify(out))
console.log(`Wrote ${counties.length} county paths → ${path.relative(root, outPath)}`)