const STATUS_STYLES = {
  green:  { bg: 'bg-success/15',  dot: 'bg-success',  text: 'text-success'  },
  yellow: { bg: 'bg-warning/15', dot: 'bg-warning', text: 'text-warning' },
  red:    { bg: 'bg-destructive/15',    dot: 'bg-destructive',    text: 'text-destructive'    },
}

function CurrentStatus({ current_status }) {
  const quality = current_status.score >= 0.7
    ? 'green'
    : current_status.score >= 0.4 ? 'yellow' : 'red'
  const styles = STATUS_STYLES[quality]

  const params = Object.values(current_status.parameters ?? {})
  const nonGreen = params.filter(p => p.score < 0.7)
  const displayParams = nonGreen.length > 0 ? nonGreen : params
  const reason = displayParams.map(p => p.description).join(' · ')

  return (
    <div className={`${styles.bg} rounded-2xl p-5 mb-4 flex items-center gap-4`}>
      <div className={`w-3 h-3 rounded-full ${styles.dot} animate-pulse flex-shrink-0`} />
      <div>
        <p className={`text-sm font-medium ${styles.text} mb-0.5`}>
          {quality === 'green' ? 'Good conditions right now'
           : quality === 'yellow' ? 'Fair conditions right now'
           : 'Poor conditions right now'}
        </p>
        <p className="text-xs text-muted-foreground">{reason}</p>
      </div>
    </div>
  )
}

export default CurrentStatus