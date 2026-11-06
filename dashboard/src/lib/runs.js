export function groupIntoRuns(incidents, gapSeconds = 60) {
  const runs = []

  for (const incident of incidents) {
    const time = new Date(incident.timestamp).getTime()
    const current = runs[runs.length - 1]

    const belongsToCurrent =
      current &&
      current.source === incident.source &&
      current.oldest - time <= gapSeconds * 1000

    if (belongsToCurrent) {
      current.incidents.push(incident)
      current.oldest = time
    } else {
      runs.push({
        id: incident.id,
        source: incident.source,
        newest: time,
        oldest: time,
        incidents: [incident],
      })
    }
  }

  return runs
}