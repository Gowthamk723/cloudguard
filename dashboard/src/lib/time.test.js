import { describe, it, expect } from 'vitest'
import { timeAgo } from './time'

const NOW = 1_000_000_000_000

describe('timeAgo', () => {
  it('says just now under a minute', () => {
    expect(timeAgo(NOW - 20_000, NOW)).toBe('just now')
  })

  it('uses hours and days', () => {
    expect(timeAgo(NOW - 3 * 3_600_000, NOW)).toBe('3h ago')
    expect(timeAgo(NOW - 50 * 3_600_000, NOW)).toBe('2d ago')
  })
})