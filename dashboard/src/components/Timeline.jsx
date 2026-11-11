import { useState } from 'react'
import RunCard from './RunCard'

const PAGE = 8

export default function Timeline({ runs }) {
  const [visible, setVisible] = useState(PAGE)
  return (
    <section aria-label="Scan history">
      <h2 className="section-title">Scan history</h2>
      <ol className="timeline">
        {runs.slice(0, visible).map((run) => (
          <RunCard key={run.id} run={run} />
        ))}
      </ol>
      {visible < runs.length && (
        <button className="more" onClick={() => setVisible((v) => v + PAGE)}>
          Show {Math.min(PAGE, runs.length - visible)} more
        </button>
      )}
    </section>
  )
}