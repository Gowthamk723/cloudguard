import { describeFinding } from '../lib/rules'

export default function FindingRow({ incident }) {
  const { label, severity } = describeFinding(incident)
  return (
    <li className={`finding finding--${severity.toLowerCase()}`}>
      <span className="finding__badge">{severity === 'FIXED' ? 'AUTO-FIXED' : severity}</span>
      <span className="finding__label">{label}</span>
      <code className="finding__resource">{incident.resource}</code>
    </li>
  )
}