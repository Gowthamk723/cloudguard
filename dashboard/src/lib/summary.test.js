import { describe, it, expect } from 'vitest'
import { summarizeRun, summarizeAll } from './summary'

const run = (source, statuses, newest = 1000) => ({
  id: 'r',
  source,
  newest,
  oldest: newest,
  incidents: statuses.map((status) => ({ status })),
})

describe('summarizeRun', () => {
  it('counts each status', () => {
    expect(summarizeRun(run('ci', ['fixed', 'flagged', 'compliant']))).toEqual({
      flagged: 1, fixed: 1, compliant: 1,
    })
  })

  it('counts error as needs review', () => {
    expect(summarizeRun(run('ci', ['error', 'flagged'])).flagged).toBe(2)
  })
})

describe('summarizeAll', () => {
  it('returns no latest run for no data', () => {
    expect(summarizeAll([])).toEqual({ latest: null, totalRuns: 0, totalFixed: 0 })
  })
})