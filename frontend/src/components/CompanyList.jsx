import { useState } from 'react'

export default function CompanyList({ companies, onAdd, onDelete }) {
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim() || !url.trim()) return
    setLoading(true)
    await onAdd(name.trim(), url.trim())
    setName('')
    setUrl('')
    setLoading(false)
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 h-full flex flex-col">
      <h2 className="text-base font-semibold mb-4">Companies ({companies.length})</h2>

      <form onSubmit={handleSubmit} className="space-y-2 mb-4 shrink-0">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Company name"
          className="w-full px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://company.com"
          type="url"
          className="w-full px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={loading || !name.trim() || !url.trim()}
          className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 dark:disabled:bg-blue-800 text-white rounded-lg font-medium text-sm transition-colors"
        >
          {loading ? 'Adding…' : '+ Add Company'}
        </button>
      </form>

      <div className="overflow-y-auto flex-1 space-y-1 -mx-1">
        {companies.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-6">No companies yet</p>
        ) : (
          companies.map((company) => (
            <div
              key={company.id}
              className="flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 group transition-colors"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate">{company.name}</p>
                <p className="text-xs text-gray-400 truncate">{company.url}</p>
              </div>
              <button
                onClick={() => onDelete(company.id)}
                title="Remove"
                className="shrink-0 text-gray-300 dark:text-gray-600 hover:text-red-500 dark:hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all text-xl leading-none font-light"
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
