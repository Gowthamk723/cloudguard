const NEEDS_REVIEW = new Set(['flagged', 'error'])

export function summarizeRun(run) {
  const counts = { flagged: 0, fixed: 0, compliant: 0 }
  for (const incident of run.incidents) {
    if (incident.status === 'fixed') counts.fixed++
    else if (incident.status === 'compliant') counts.compliant++
    else if (NEEDS_REVIEW.has(incident.status)) counts.flagged++
  }
  return counts
}

export function summarizeAll(runs) {
  const latest = runs[0]
  return {
    latest: latest
      ? { ...summarizeRun(latest), source: latest.source, time: latest.newest }
      : null,
    totalRuns: runs.length,
    totalFixed: runs.reduce((sum, run) => sum + summarizeRun(run).fixed, 0),
  }
}