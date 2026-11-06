import { describe, it, expect } from 'vitest'
import { groupIntoRuns } from './runs'

const inc = (id, iso, source = 'ci') => ({ id, source, timestamp: iso })

describe('groupIntoRuns', () => {
  it('returns no runs for no incidents', () => {
    expect(groupIntoRuns([])).toEqual([])
  })

  it('groups incidents seconds apart into one run', () => {
    const runs = groupIntoRuns([
      inc('3', '2026-11-05T10:18:13+00:00'),
      inc('2', '2026-11-05T10:18:12+00:00'),
      inc('1', '2026-11-05T10:18:10+00:00'),
    ])
    expect(runs).toHaveLength(1)
    expect(runs[0].incidents).toHaveLength(3)
  })

  it('splits runs that are far apart', () => {
    const runs = groupIntoRuns([
      inc('2', '2026-11-05T10:18:13+00:00'),
      inc('1', '2026-11-04T10:24:27+00:00'),
    ])
    expect(runs).toHaveLength(2)
  })

  it('splits runs from different sources even if simultaneous', () => {
    const runs = groupIntoRuns([
      inc('2', '2026-11-05T10:18:13+00:00', 'ci'),
      inc('1', '2026-11-05T10:18:12+00:00', 'local'),
    ])
    expect(runs).toHaveLength(2)
  })
})