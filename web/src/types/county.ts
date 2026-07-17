export interface CountySummary {
  slug: string
  name: string
  members: number | null
  selection_method: string | null
}

export interface CountyDetail extends CountySummary {
  meeting_schedule: string | null
  body_html: string
}
