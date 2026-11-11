import { describe, it, expect } from 'vitest'
import { runCost, formatUsd } from './cost'

const run = (incidents) => ({ incidents })

describe('runCost', () => {
  it('sums estimates of flagged findings', () => {
    expect(runCost(run([
      { status: 'flagged', estimated_monthly_usd: 0.5 },
      { status: 'flagged', estimated_monthly_usd: 0.25 },
    ]))).toBe(0.75)
  })

  it('ignores compliant findings and missing estimates', () => {
    expect(runCost(run([
      { status: 'compliant', estimated_monthly_usd: 9 },
      { status: 'flagged', estimated_monthly_usd: null },
      { status: 'flagged' },
    ]))).toBe(0)
  })
})

describe('formatUsd', () => {
  it('returns null for missing values', () => {
    expect(formatUsd(null)).toBeNull()
  })
  it('shows <$0.01 for tiny amounts', () => {
    expect(formatUsd(0.0000898)).toBe('<$0.01')
  })
  it('formats normal amounts', () => {
    expect(formatUsd(12.5)).toBe('$12.50')
  })
})