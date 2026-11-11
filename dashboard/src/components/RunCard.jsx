import SourceChip from './SourceChip'
import FindingRow from './FindingRow'
import { sortFindings, worstSeverity } from '../lib/rules'
import { timeAgo } from '../lib/time'

export default function RunCard({ run }) {
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
          {sortFindings(run.incidents).map((incident) => (
            <FindingRow key={incident.id} incident={incident} />
          ))}
        </ul>
      </article>
    </li>
  )
}