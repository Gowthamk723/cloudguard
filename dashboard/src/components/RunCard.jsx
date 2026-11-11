import { useState } from 'react'
import SourceChip from './SourceChip'
import FindingRow from './FindingRow'
import { describeFinding, sortFindings, worstSeverity } from '../lib/rules'
import { timeAgo } from '../lib/time'

export default function RunCard({ run }) {
  const [showOk, setShowOk] = useState(false)
  const sorted = sortFindings(run.incidents)
  const isOk = (i) => describeFinding(i).severity === 'OK'
  const okCount = sorted.filter(isOk).length
  const visible = showOk ? sorted : sorted.filter((i) => !isOk(i))
  const worst = worstSeverity(run.incidents).toLowerCase()
  const date = new Date(run.newest)

  return (
    <li className="run">
      <span className={`run__dot run__dot--${worst}`} aria-hidden="true" />
      <article className="run__card">
        <header className="run__head">
          <SourceChip source={run.source} />
          <time dateTime={date.toISOString()} title={date.toLocaleString()}>
            {timeAgo(run.newest)}
          </time>
        </header>
        <ul className="findings">
          {visible.map((incident) => (
            <FindingRow key={incident.id} incident={incident} />
          ))}
        </ul>
        {okCount > 0 && (
          <button className="toggle" onClick={() => setShowOk((v) => !v)}>
            {showOk ? 'Hide' : 'Show'} {okCount} compliant
          </button>
        )}
      </article>
    </li>
  )
}