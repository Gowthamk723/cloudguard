import { useIncidents } from './hooks/useIncidents'

export default function App() {
  const { status, runs, error } = useIncidents()

  if (status === 'loading') return <p>Loading…</p>
  if (status === 'error') return <p>Could not load incidents: {error}</p>

  return (
    <main>
      <h1>CloudGuard</h1>
      <p>{runs.length} scan runs</p>
      <ul>
        {runs.map((run) => (
          <li key={run.id}>
            [{run.source}] {new Date(run.newest).toLocaleString()} — {run.incidents.length} findings
          </li>
        ))}
      </ul>
    </main>
  )
}