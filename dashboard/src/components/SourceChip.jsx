export default function SourceChip({ source }) {
  const isCi = source === 'ci'
  return (
    <span className={`chip ${isCi ? 'chip--ci' : 'chip--local'}`}>
      {isCi ? 'CI' : 'LOCAL'}
    </span>
  )
}