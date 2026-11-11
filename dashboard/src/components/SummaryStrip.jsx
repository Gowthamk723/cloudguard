import SourceChip from './SourceChip'
import { timeAgo } from '../lib/time'
import { formatUsd } from '../lib/cost'

const STATS = [
  { key: 'flagged', label: 'Needs review' },
  { key: 'fixed', label: 'Auto-fixed' },
  { key: 'compliant', label: 'Compliant' },
]

export default function SummaryStrip({ summary }) {
  const { latest, totalRuns, totalFixed } = summary

  if (!latest) return <p className="empty">No scans recorded yet.</p>

  return (
    <section className="strip" aria-label="Latest scan summary">
      <header className="strip__head">
        <h2>Latest scan</h2>
        <SourceChip source={latest.source} />
        <span className="strip__time">{timeAgo(latest.time)}</span>
      </header>

      <div className="strip__stats">
        {STATS.map(({ key, label }) => (
          <div key={key} className={`stat stat--${key}`}>
            <span className="stat__value">{latest[key]}</span>
            <span className="stat__label">{label}</span>
          </div>
        ))}
      </div>

      {latest.cost > 0 && (
        <p className="strip__cost">
          Estimated storage cost with no expiry policy:{' '}
          <strong>{formatUsd(latest.cost)}</strong> / month
          <span> · an estimate, assumptions in the README</span>
        </p>
      )}

      <footer className="strip__foot">
        {totalRuns} scans tracked · {totalFixed} issues auto-fixed all time
      </footer>
    </section>
  )
}