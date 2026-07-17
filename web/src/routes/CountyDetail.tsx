import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { fetchCounty } from '../lib/api'

export function CountyDetail() {
  const { slug } = useParams<{ slug: string }>()
  const { data, isLoading, error } = useQuery({
    queryKey: ['county', slug],
    queryFn: () => fetchCounty(slug!),
    enabled: Boolean(slug),
  })

  if (isLoading) return <p className="p-4">Loading…</p>
  if (error) return <p className="p-4 text-red-600">Failed to load this county.</p>

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">{data!.name} County Board of Elections</h1>
      <dl className="mt-4 grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1">
        <dt className="font-semibold">Members</dt>
        <dd>{data!.members ?? '—'}</dd>
        <dt className="font-semibold">Selection method</dt>
        <dd>{data!.selection_method ?? '—'}</dd>
        <dt className="font-semibold">Meeting schedule</dt>
        <dd>{data!.meeting_schedule ?? '—'}</dd>
      </dl>
      <div className="mt-4 prose" dangerouslySetInnerHTML={{ __html: data!.body_html }} />
    </div>
  )
}
