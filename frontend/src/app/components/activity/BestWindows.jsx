const WINDOW_STYLES = {
  green:  { bg: 'bg-success/15',  text: 'text-success' },
  yellow: { bg: 'bg-muted',   text: 'text-muted-foreground'  },
  red:    { bg: 'bg-destructive/15',    text: 'text-destructive'   },
}

/*
  Formats "2026-10-20T10:00:00+00:00" → "10:00"
*/
function formatTime(isoString) {
  const date = new Date(isoString)
  return date.toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Europe/Paris'
  })
}

function BestWindows({ best_window }) {
  return (
    <div className="glass border border-border rounded-2xl p-5 mb-4">
      <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-primary mb-4">Best window today</p>

      {!best_window || best_window.length === 0 ? (
        <div className="bg-muted rounded-lg p-4 text-center">
          <p className="text-sm text-muted-foreground">No ideal window today</p>
        </div>
      ) : (
        <div className="flex gap-3">
          {best_window.map((window, index) => {
            const styles = WINDOW_STYLES[index === 0 ? 'green' : 'yellow']
            return (
              <div key={index} className={`flex-1 ${styles.bg} rounded-lg p-4 text-center`}>
                <p className={`text-lg font-medium ${styles.text} mb-1`}>
                  {formatTime(window.from)} – {formatTime(window.to)}
                </p>
                <p className="text-xs text-muted-foreground">{window.reason}</p>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default BestWindows