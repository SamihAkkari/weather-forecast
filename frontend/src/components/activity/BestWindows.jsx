const WINDOW_STYLES = {
  green:  { bg: 'bg-green-50',  text: 'text-green-700' },
  yellow: { bg: 'bg-gray-50',   text: 'text-gray-500'  },
  red:    { bg: 'bg-red-50',    text: 'text-red-600'   },
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
    <div className="border border-gray-100 rounded-xl p-5 mb-4">
      <p className="text-xs text-gray-400 mb-3">Best window today</p>

      {!best_window || best_window.length === 0 ? (
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-400">No good window today</p>
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
                <p className="text-xs text-gray-400">{window.reason}</p>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default BestWindows