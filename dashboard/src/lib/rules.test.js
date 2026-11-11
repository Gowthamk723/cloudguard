import { describe, it, expect } from 'vitest'
import { describeFinding, sortFindings, worstSeverity } from './rules'

const f = (rule, status) => ({ id: rule + status, rule, status })

describe('describeFinding', () => {
  it('marks fixed items as FIXED regardless of rule severity', () => {
    expect(describeFinding(f('s3_kms_encryption', 'fixed')).severity).toBe('FIXED')
  })

  it('uses rule severity for flagged items', () => {
    expect(describeFinding(f('iam_wildcard_policy', 'flagged')).severity).toBe('HIGH')
  })

  it('falls back to the raw rule name and LOW for unknown rules', () => {
    expect(describeFinding(f('mystery', 'flagged'))).toEqual({ label: 'mystery', severity: 'LOW' })
  })
})

describe('sortFindings', () => {
  it('orders HIGH before LOW before FIXED without mutating the input', () => {
    const input = [
      f('s3_kms_encryption', 'fixed'),
      f('s3_required_tag', 'flagged'),
      f('iam_wildcard_policy', 'flagged'),
    ]
    const sorted = sortFindings(input)
    expect(sorted.map((i) => i.rule)).toEqual([
      'iam_wildcard_policy', 's3_required_tag', 's3_kms_encryption',
    ])
    expect(input[0].rule).toBe('s3_kms_encryption')
  })
})

describe('worstSeverity', () => {
  it('returns the highest severity in a run', () => {
    expect(worstSeverity([f('s3_required_tag', 'flagged'), f('iam_wildcard_policy', 'flagged')])).toBe('HIGH')
  })
})