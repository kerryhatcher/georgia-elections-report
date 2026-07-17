import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchCounties } from '../lib/api'

export function CountiesList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['counties'],
    queryFn: fetchCounties,
  })

  if (isLoading) return <p className="p-4">Loading counties…</p>
  if (error) return <p className="p-4 text-red-600">Failed to load counties.</p>

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">County Boards of Elections</h1>
      <table className="w-full border-collapse">
        <thead>
          <tr className="text-left border-b">
            <th className="py-2">County</th>
            <th className="py-2">Members</th>
            <th className="py-2">Selection Method</th>
          </tr>
        </thead>
        <tbody>
          {data!.map((county) => (
            <tr key={county.slug} className="border-b">
              <td className="py-2">
                <Link className="text-blue-600 underline" to={`/counties/${county.slug}`}>
                  {county.name}
                </Link>
              </td>
              <td className="py-2">{county.members ?? '—'}</td>
              <td className="py-2">{county.selection_method ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
