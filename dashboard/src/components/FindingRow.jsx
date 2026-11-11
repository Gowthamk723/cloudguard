import { describeFinding } from '../lib/rules'
import { formatUsd } from '../lib/cost'

export default function FindingRow({ incident }) {
  const { label, severity } = describeFinding(incident)
  const cost = formatUsd(incident.estimated_monthly_usd)
  return (
    <li className={`finding finding--${severity.toLowerCase()}`}>
      <span className="finding__badge">{severity === 'FIXED' ? 'AUTO-FIXED' : severity}</span>
      <span className="finding__label">
        {label}
        {cost && <em className="finding__cost"> · est. {cost}/mo</em>}
      </span>
      <code className="finding__resource">{incident.resource}</code>
    </li>
  )
}