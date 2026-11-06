import { useMemo } from 'react'
import { useIncidents } from './hooks/useIncidents'
import { summarizeAll } from './lib/summary'
import SummaryStrip from './components/SummaryStrip'
import SourceChip from './components/SourceChip'

export default function App() {
  const { status, runs, error } = useIncidents()
  const summary = useMemo(() => summarizeAll(runs), [runs])

  return (
    <main className="page">
      <h1 className="brand">CloudGuard</h1>

      {status === 'loading' && <p className="empty">Loading…</p>}
      {status === 'error' && <p className="empty empty--error">Could not load incidents: {error}</p>}

      {status === 'ready' && (
        <>
          <SummaryStrip summary={summary} />
          {/* Temporary list until the timeline lands in Part 4 */}
          <ul className="runs">
            {runs.map((run) => (
              <li key={run.id}>
                <SourceChip source={run.source} />{' '}
                {new Date(run.newest).toLocaleString()} · {run.incidents.length} findings
              </li>
            ))}
          </ul>
        </>
      )}
    </main>
  )
}