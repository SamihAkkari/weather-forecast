import { useState } from 'react'

const BAR_COLORS = {
  green:  '#16a34a',
  yellow: '#facc15',
  red:    '#ef4444',
}

/*
  Formats ISO string to hour label: "2026-10-20T14:00:00+00:00" → "14:00"
*/
function formatHour(isoString) {
  const date = new Date(isoString)
  return `${String(date.getUTCHours()).padStart(2, '0')}:${String(date.getUTCMinutes()).padStart(2, '0')}`
  // return date.toLocaleTimeString('fr-FR', {
  //   hour: '2-digit',
  //   minute: '2-digit',
  //   timeZone: 'Europe/Paris'
  // })
}


function Tooltip({ parameters }) {
  const entries = Object.entries(parameters)

  const DOT_COLORS = {
    green:  'bg-green-400',
    yellow: 'bg-yellow-400',
    red:    'bg-red-400',
  }

  return (
    <div className="absolute left-10 bottom-full mb-2 z-10 bg-white border border-gray-100 rounded-xl shadow-lg p-3 min-w-52">
      <div className="flex flex-col gap-2">
        {entries.map(([key, param]) => (
          <div key={key} className="flex items-start gap-2">
            <div className={`w-2 h-2 rounded-full mt-0.5 flex-shrink-0 ${DOT_COLORS[param.status] ?? 'bg-gray-300'}`} />
            <div>
              <span className="text-xs font-medium text-gray-600 capitalize">{key}: </span>
              <span className="text-xs text-gray-400">{param.description}</span>
            </div>
          </div>
        ))}
      </div>
      {/* Small triangle pointing down */}
      <div className="absolute left-4 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-white" />
    </div>
  )
}

function HourlyRow({ entry }) {
  const [showTooltip, setShowTooltip] = useState(false)

  return (
    /*
      The tooltip uses absolute positioning
      relative to this row, not the page.
    */
    <div
      className="relative flex items-center gap-3 cursor-pointer"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <span className="text-xs text-gray-400 w-10 flex-shrink-0">
        {formatHour(entry.time)}
      </span>

      <div className="flex-1 h-2 bg-gray-100 rounded-full">
        <div
          className="h-2 rounded-full transition-all"
          style={{
            width:      `${Math.round(entry.score * 100)}%`,
            background: BAR_COLORS[entry.status] ?? BAR_COLORS.yellow,
          }}
        />
      </div>

      {showTooltip && entry.parameters && (
        <Tooltip parameters={entry.parameters} />
      )}
    </div>
  )
}

function HourlyTimeline({ hourly }) {
  return (
    <div className="border border-gray-100 rounded-xl p-5">
      <p className="text-xs text-gray-400 mb-4">Hourly outlook</p>
      <div className="flex flex-col gap-3">
        {hourly.map((entry, index) => (
          <HourlyRow key={index} entry={entry} />
        ))}
      </div>
    </div>
  )
}

export default HourlyTimeline