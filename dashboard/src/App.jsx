import { useMemo } from 'react'
import { useIncidents } from './hooks/useIncidents'
import { summarizeAll } from './lib/summary'
import SummaryStrip from './components/SummaryStrip'
import Timeline from './components/Timeline'

export default function App() {
  const { status, runs, error } = useIncidents()
  const summary = useMemo(() => summarizeAll(runs), [runs])

  return (
    <main className="page">
      <h1 className="brand">CloudGuard</h1>

      {status === 'loading' && (
        <div className="skeleton" aria-busy="true" aria-label="Loading scans">
          <div className="skeleton__block" />
          <div className="skeleton__block" />
        </div>
      )}
      {status === 'error' && (
        <p className="empty empty--error">Could not load incidents: {error}</p>
      )}
      {status === 'ready' && (
        <>
          <SummaryStrip summary={summary} />
          <Timeline runs={runs} />
        </>
      )}
    </main>
  )
}