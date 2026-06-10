export default function Controls({ onScrape, onSendEmail, status, isScraping, isSendingEmail }) {
  const lastRun = status.last_run
    ? new Date(status.last_run).toLocaleString()
    : 'Never'

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 flex flex-wrap items-center gap-3">
      <button
        onClick={onScrape}
        disabled={isScraping || isSendingEmail}
        className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 dark:disabled:bg-blue-800 text-white rounded-lg font-semibold text-sm transition-colors"
      >
        {isScraping ? (
          <>
            <Spinner />
            Scraping…
          </>
        ) : (
          '▶ Run Scraper'
        )}
      </button>

      <button
        onClick={onSendEmail}
        disabled={isSendingEmail || isScraping}
        className="flex items-center gap-2 px-5 py-2.5 bg-violet-600 hover:bg-violet-700 disabled:bg-violet-400 dark:disabled:bg-violet-800 text-white rounded-lg font-semibold text-sm transition-colors"
      >
        {isSendingEmail ? (
          <>
            <Spinner />
            Sending…
          </>
        ) : (
          '📧 Send Email Digest'
        )}
      </button>

      <div className="ml-auto flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
        <span
          className={`inline-block w-2.5 h-2.5 rounded-full shrink-0 ${
            isScraping ? 'bg-green-500 animate-pulse' : 'bg-gray-300 dark:bg-gray-600'
          }`}
        />
        {isScraping ? (
          <span className="text-green-600 dark:text-green-400 font-medium">Scraping in progress…</span>
        ) : (
          <span>Last run: {lastRun}</span>
        )}
      </div>
    </div>
  )
}

function Spinner() {
  return (
    <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
  )
}
