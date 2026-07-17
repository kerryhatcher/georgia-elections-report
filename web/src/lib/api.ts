import type { CountyDetail, CountySummary } from '../types/county'

async function getJson<T>(path: string): Promise<T> {
  // Prepend Vite's configured base URL so requests resolve correctly whether
  // the app is served from the domain root or a project subpath (e.g. GitHub
  // Pages). BASE_URL is '/' by default and set at build time via Vite `base`.
  const url = `${import.meta.env.BASE_URL}${path.replace(/^\//, '')}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Request to ${url} failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function fetchCounties(): Promise<CountySummary[]> {
  return getJson<CountySummary[]>('/data/counties.json')
}

export function fetchCounty(slug: string): Promise<CountyDetail> {
  return getJson<CountyDetail>(`/data/counties/${slug}.json`)
}
