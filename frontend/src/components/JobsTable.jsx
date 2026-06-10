import { useMemo, useState } from 'react'

const SOURCE_BADGE = {
  greenhouse: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  lever: 'bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300',
  ashby: 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
  scraped: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
}

const WORK_MODE_BADGE = {
  remote: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
  hybrid: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  'on-site': 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
}

const EXP_BADGE = {
  entry: 'bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300',
  mid: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300',
  senior: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
}

function fmt(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function Badge({ text, colorMap, fallback = '' }) {
  if (!text) return null
  const cls = colorMap[text] ?? fallback
  if (!cls) return null
  return (
    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-md capitalize ${cls}`}>
      {text}
    </span>
  )
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
        (j.location || '').toLowerCase().includes(q) ||
        (j.work_mode || '').toLowerCase().includes(q) ||
        (j.work_type || '').toLowerCase().includes(q) ||
        j.source.toLowerCase().includes(q),
    )
  }, [jobs, search])

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex flex-wrap items-center gap-3">
        <h2 className="text-base font-semibold">Jobs Found</h2>
        <span className="bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold px-2 py-0.5 rounded-full">
          {filtered.length}
        </span>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search title, company, location…"
          className="ml-auto px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 w-60"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        {filtered.length === 0 ? (
          <div className="py-16 text-center text-gray-400 text-sm">
            {jobs.length === 0
              ? 'No jobs found yet. Run the scraper to get started.'
              : 'No jobs match your search.'}
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-750 text-left">
                {['Company', 'Job Title', 'Details', 'Source', 'Found At', 'Apply'].map((h) => (
                  <th key={h} className="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {filtered.map((job) => (
                <tr key={job.id} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">

                  {/* Company */}
                  <td className="px-4 py-3 font-medium whitespace-nowrap">{job.company_name}</td>

                  {/* Title */}
                  <td className="px-4 py-3 max-w-xs">
                    <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{job.title}</p>
                    {job.location && (
                      <p className="text-xs text-gray-400 mt-0.5 truncate">📍 {job.location}</p>
                    )}
                  </td>

                  {/* Details — work mode, work type, experience as badges */}
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      <Badge text={job.work_mode} colorMap={WORK_MODE_BADGE} />
                      {job.work_type && (
                        <span className="text-xs font-semibold px-1.5 py-0.5 rounded-md capitalize bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                          {job.work_type}
                        </span>
                      )}
                      <Badge text={job.experience} colorMap={EXP_BADGE} />
                    </div>
                  </td>

                  {/* Source */}
                  <td className="px-4 py-3">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${SOURCE_BADGE[job.source] ?? SOURCE_BADGE.scraped}`}>
                      {job.source}
                    </span>
                  </td>

                  {/* Found At */}
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400 text-xs whitespace-nowrap">
                    {fmt(job.found_at)}
                  </td>

                  {/* Apply */}
                  <td className="px-4 py-3">
                    {job.url ? (
                      <a href={job.url} target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-colors whitespace-nowrap">
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
