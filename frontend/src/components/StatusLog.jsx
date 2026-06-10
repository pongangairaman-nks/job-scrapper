import { useEffect, useRef } from 'react'

export default function StatusLog({ log, isActive }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [log.length])

  const fmt = (iso) => {
    if (!iso) return ''
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-700 p-4">
      <div className="flex items-center gap-2 mb-3">
        <span
          className={`w-2 h-2 rounded-full shrink-0 ${
            isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-600'
          }`}
        />
        <span className="text-sm font-semibold text-gray-300">Scraper Log</span>
        {isActive && (
          <span className="ml-1 text-xs text-green-400 font-medium">Running…</span>
        )}
      </div>

      <div className="font-mono text-xs space-y-1 max-h-52 overflow-y-auto pr-1">
        {log.length === 0 ? (
          <p className="text-gray-600">{isActive ? 'Starting…' : 'No entries yet'}</p>
        ) : (
          log.map((entry, i) => (
            <div key={i} className="flex gap-3 leading-5">
              <span className="text-gray-600 shrink-0 tabular-nums">{fmt(entry.time)}</span>
              <span className="text-gray-300 break-all">{entry.message}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
