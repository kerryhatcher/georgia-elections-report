// Astro does not prefix internal links with `base` automatically; every
// internal href must go through this helper. BASE_URL is '/georgia-elections-report'
// in this project (may or may not carry a trailing slash depending on config).
const base = import.meta.env.BASE_URL.replace(/\/+$/, '')

export function href(path: string): string {
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}
