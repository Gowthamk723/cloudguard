export function runCost(run) {
  return run.incidents.reduce(
    (sum, i) =>
      sum + (i.status === 'flagged' && typeof i.estimated_monthly_usd === 'number'
        ? i.estimated_monthly_usd
        : 0),
    0,
  )
}

export function formatUsd(value) {
  if (value == null) return null
  if (value === 0) return '$0.00'
  if (value < 0.01) return '<$0.01'
  return `$${value.toFixed(2)}`
}