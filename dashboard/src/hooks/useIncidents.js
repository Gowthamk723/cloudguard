import { useEffect, useState } from 'react'
import { groupIntoRuns } from '../lib/runs'

export function useIncidents() {
  const [state, setState] = useState({ status: 'loading', runs: [], error: null })

  useEffect(() => {
    let cancelled = false

    fetch('/api/incidents?limit=500')
      .then((res) => {
        if (!res.ok) throw new Error(`API returned ${res.status}`)
        return res.json()
      })
      .then((data) => {
        if (!cancelled) {
          setState({ status: 'ready', runs: groupIntoRuns(data.incidents), error: null })
        }
      })
      .catch((err) => {
        if (!cancelled) setState({ status: 'error', runs: [], error: err.message })
      })

    return () => {
      cancelled = true
    }
  }, [])

  return state
}