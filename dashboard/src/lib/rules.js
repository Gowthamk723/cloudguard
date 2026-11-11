export const RULES = {
  s3_kms_encryption: { label: 'S3 bucket not using KMS encryption', severity: 'HIGH' },
  iam_wildcard_policy: { label: 'IAM role with wildcard policy', severity: 'HIGH' },
  s3_no_lifecycle: { label: 'Bucket has no lifecycle policy', severity: 'MEDIUM' },
  s3_required_tag: { label: "Missing 'Environment' tag", severity: 'LOW' },
  s3_idle_bucket: { label: 'Idle bucket (no objects)', severity: 'LOW' },
}

const RANK = { HIGH: 0, MEDIUM: 1, LOW: 2, FIXED: 3, OK: 4 }

export function describeFinding(incident) {
  const rule = RULES[incident.rule]
  let severity
  if (incident.status === 'fixed') severity = 'FIXED'
  else if (incident.status === 'compliant') severity = 'OK'
  else severity = rule ? rule.severity : 'LOW'
  return { label: rule ? rule.label : incident.rule, severity }
}

export function sortFindings(incidents) {
  return [...incidents].sort(
    (a, b) => RANK[describeFinding(a).severity] - RANK[describeFinding(b).severity],
  )
}

export function worstSeverity(incidents) {
  const sorted = sortFindings(incidents)
  return sorted.length ? describeFinding(sorted[0]).severity : 'OK'
}