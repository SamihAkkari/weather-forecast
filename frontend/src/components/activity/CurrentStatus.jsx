const STATUS_STYLES = {
  green:  { bg: 'bg-green-50',  dot: 'bg-green-400',  text: 'text-green-700'  },
  yellow: { bg: 'bg-yellow-50', dot: 'bg-yellow-400', text: 'text-yellow-700' },
  red:    { bg: 'bg-red-50',    dot: 'bg-red-400',    text: 'text-red-600'    },
}

function CurrentStatus({ current_status }) {
  const styles = STATUS_STYLES[current_status.status] ?? STATUS_STYLES.yellow

  const params = Object.values(current_status.parameters ?? {})
  const nonGreen = params.filter(p => p.status !== 'green')
  const displayParams = nonGreen.length > 0 ? nonGreen : params
  const reason = displayParams.map(p => p.description).join(' · ')

  return (
    <div className={`${styles.bg} rounded-xl p-5 mb-4 flex items-center gap-4`}>
      <div className={`w-3 h-3 rounded-full ${styles.dot} animate-pulse flex-shrink-0`} />
      <div>
        <p className={`text-sm font-medium ${styles.text} mb-0.5`}>
          {current_status.status === 'green' ? 'Good conditions right now'
           : current_status.status === 'yellow' ? 'Fair conditions right now'
           : 'Poor conditions right now'}
        </p>
        <p className="text-xs text-gray-400">{reason}</p>
      </div>
    </div>
  )
}

export default CurrentStatus