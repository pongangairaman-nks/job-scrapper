import { useMemo, useState } from 'react'

const SOURCE_BADGE = {
  greenhouse:
    'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  lever:
    'bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300',
  ashby:
    'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
  scraped:
    'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
}

function fmt(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function JobsTable({ jobs }) {
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return jobs
    return jobs.filter(
      (j) =>
        j.title.toLowerCase().includes(q) ||
        j.company_name.toLowerCase().includes(q) ||
        j.source.toLowerCase().includes(q),
    )
  }, [jobs, search])

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex flex-wrap items-center gap-3">
        <h2 className="text-base font-semibold">Jobs Found</h2>
        <span className="bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold px-2 py-0.5 rounded-full">
          {filtered.length}
        </span>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search title, company, source…"
          className="ml-auto px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 w-56"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto flex-1">
        {filtered.length === 0 ? (
          <div className="py-16 text-center text-gray-400 text-sm">
            {jobs.length === 0
              ? 'No jobs found yet. Run the scraper to get started.'
              : 'No jobs match your search.'}
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-750 text-left sticky top-0">
                {['Company', 'Job Title', 'Source', 'Found At', 'Apply'].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide whitespace-nowrap"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {filtered.map((job) => (
                <tr
                  key={job.id}
                  className="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                >
                  <td className="px-4 py-3 font-medium whitespace-nowrap">{job.company_name}</td>
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300 max-w-xs truncate">
                    {job.title}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${
                        SOURCE_BADGE[job.source] ?? SOURCE_BADGE.scraped
                      }`}
                    >
                      {job.source}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400 text-xs whitespace-nowrap">
                    {fmt(job.found_at)}
                  </td>
                  <td className="px-4 py-3">
                    {job.url ? (
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-colors whitespace-nowrap"
                      >
                        Apply →
                      </a>
                    ) : (
                      <span className="text-gray-300 dark:text-gray-600 text-xs">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
