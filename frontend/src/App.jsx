import { useCallback, useEffect, useRef, useState } from 'react'
import CompanyList from './components/CompanyList'
import Controls from './components/Controls'
import JobsTable from './components/JobsTable'
import StatusLog from './components/StatusLog'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const EMPTY_STATUS = {
  is_scraping: false,
  last_run: null,
  jobs_count: 0,
  companies_count: 0,
  jobs_found_this_run: 0,
  log: [],
}

export default function App() {
  const [companies, setCompanies] = useState([])
  const [jobs, setJobs] = useState([])
  const [status, setStatus] = useState(EMPTY_STATUS)
  const [isScraping, setIsScraping] = useState(false)
  const [isSendingEmail, setIsSendingEmail] = useState(false)
  const [toast, setToast] = useState(null)
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('theme')
    if (saved) return saved === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  const pollRef = useRef(null)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
  }, [isDark])

  const fetchCompanies = useCallback(async () => {
    try {
      const r = await fetch(`${API}/companies`)
      if (r.ok) setCompanies(await r.json())
    } catch (_) {}
  }, [])

  const fetchJobs = useCallback(async () => {
    try {
      const r = await fetch(`${API}/jobs`)
      if (r.ok) setJobs(await r.json())
    } catch (_) {}
  }, [])

  const fetchStatus = useCallback(async () => {
    try {
      const r = await fetch(`${API}/status`)
      if (r.ok) setStatus(await r.json())
    } catch (_) {}
  }, [])

  useEffect(() => {
    fetchCompanies()
    fetchJobs()
    fetchStatus()
  }, [])

  // Poll /status every 2s while scraping
  useEffect(() => {
    if (isScraping) {
      pollRef.current = setInterval(fetchStatus, 2000)
    } else {
      clearInterval(pollRef.current)
    }
    return () => clearInterval(pollRef.current)
  }, [isScraping, fetchStatus])

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 4000)
  }

  const handleScrape = async () => {
    setIsScraping(true)
    try {
      const r = await fetch(`${API}/scrape`, { method: 'POST' })
      const data = await r.json()
      if (!r.ok) throw new Error(data.detail || 'Scrape failed')
      await Promise.all([fetchJobs(), fetchStatus()])
      showToast(`Done! ${data.count} new job(s) saved.`)
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setIsScraping(false)
    }
  }

  const handleSendEmail = async () => {
    setIsSendingEmail(true)
    try {
      const r = await fetch(`${API}/send-email`, { method: 'POST' })
      const data = await r.json()
      if (!r.ok) throw new Error(data.detail || 'Email failed')
      showToast(data.message)
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setIsSendingEmail(false)
    }
  }

  const handleAddCompany = async (name, url) => {
    const r = await fetch(`${API}/companies`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, url }),
    })
    if (r.ok) {
      await Promise.all([fetchCompanies(), fetchStatus()])
      showToast(`Added "${name}"`)
    } else {
      const d = await r.json()
      showToast(d.detail || 'Failed to add company', 'error')
    }
  }

  const handleDeleteCompany = async (id) => {
    const r = await fetch(`${API}/companies/${id}`, { method: 'DELETE' })
    if (r.ok) await Promise.all([fetchCompanies(), fetchStatus()])
  }

  const showLog = isScraping || status.log?.length > 0

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors duration-200">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-xl text-sm font-semibold max-w-sm transition-all ${
            toast.type === 'error'
              ? 'bg-red-500 text-white'
              : 'bg-emerald-500 text-white'
          }`}
        >
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-blue-600 dark:text-blue-400 leading-tight">
              Frontend Job Scraper
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Monitoring {status.companies_count} companies · {status.jobs_count} jobs in DB
            </p>
          </div>
          <button
            onClick={() => setIsDark((d) => !d)}
            className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-lg"
            aria-label="Toggle dark mode"
          >
            {isDark ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-5">
        <Controls
          onScrape={handleScrape}
          onSendEmail={handleSendEmail}
          status={status}
          isScraping={isScraping}
          isSendingEmail={isSendingEmail}
        />

        {showLog && (
          <StatusLog log={status.log ?? []} isActive={isScraping} />
        )}

        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-5 items-start">
          <CompanyList
            companies={companies}
            onAdd={handleAddCompany}
            onDelete={handleDeleteCompany}
          />
          <JobsTable jobs={jobs} />
        </div>
      </main>
    </div>
  )
}
