import type { CountyDetail, CountySummary } from '../types/county'

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(`Request to ${path} failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function fetchCounties(): Promise<CountySummary[]> {
  return getJson<CountySummary[]>('/data/counties.json')
}

export function fetchCounty(slug: string): Promise<CountyDetail> {
  return getJson<CountyDetail>(`/data/counties/${slug}.json`)
}
