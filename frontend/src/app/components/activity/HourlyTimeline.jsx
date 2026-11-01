import { useState } from 'react'
import { formatHourFr } from '../../utils/time'

const BAR_COLORS = [
  { score: 0, color: '#7f1d1d' },
  { score: 0.25, color: '#ef4444' },
  { score: 0.5, color: '#facc15' },
  { score: 0.75, color: '#86efac' },
  { score: 1, color: '#14532d' },
]

function getBarColor(score) {
  const clampedScore = Number.isFinite(score)
    ? Math.max(0, Math.min(1, score))
    : 0.5
  const upperIndex = BAR_COLORS.findIndex(stop => stop.score >= clampedScore)
  const lower = BAR_COLORS[Math.max(0, upperIndex - 1)]
  const upper = BAR_COLORS[upperIndex === -1 ? BAR_COLORS.length - 1 : upperIndex]
  const ratio = upper.score === lower.score
    ? 0
    : (clampedScore - lower.score) / (upper.score - lower.score)
  const lowerRgb = lower.color.match(/[A-Fa-f0-9]{2}/g).map(value => parseInt(value, 16))
  const upperRgb = upper.color.match(/[A-Fa-f0-9]{2}/g).map(value => parseInt(value, 16))
  const rgb = lowerRgb.map((value, index) =>
    Math.round(value + (upperRgb[index] - value) * ratio)
  )

  return `rgb(${rgb.join(', ')})`
}

/*
  Formats ISO string to hour label: "2026-10-20T14:00:00+00:00" → "14:00"
*/
// function formatHour(isoString) {
//   const date = new Date(isoString)
//   return `${String(date.getUTCHours()).padStart(2, '0')}:${String(date.getUTCMinutes()).padStart(2, '0')}`
//   // return date.toLocaleTimeString('fr-FR', {
//   //   hour: '2-digit',
//   //   minute: '2-digit',
//   //   timeZone: 'Europe/Paris'
//   // })
// }


function Tooltip({ parameters }) {
  const entries = Object.entries(parameters)

  const DOT_COLORS = {
    dark_green:   'bg-success',
    green:        'bg-success',
    light_green:  'bg-success',
    yellow_green: 'bg-success',
    yellow:       'bg-warning',
    yellow_orange:'bg-warning',
    orange:       'bg-chart-4',
    dark_orange:  'bg-chart-4',
    red:          'bg-destructive',
    dark_red:     'bg-destructive',
  }

  return (
    <div className="absolute left-10 bottom-full mb-2 z-10 glass border border-border rounded-2xl shadow-lg p-3 min-w-52">
      <div className="flex flex-col gap-2">
        {entries.map(([key, param]) => (
          <div key={key} className="flex items-start gap-2">
            <div className={`w-2 h-2 rounded-full mt-0.5 flex-shrink-0 ${DOT_COLORS[param.status] ?? 'bg-secondary'}`} />
            <div>
              <span className="text-xs font-medium text-muted-foreground capitalize">{key}: </span>
              <span className="text-xs text-muted-foreground">{param.description}</span>
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
      <span className="text-xs text-muted-foreground w-10 flex-shrink-0">
        {formatHourFr(entry.time)}
      </span>

      <div className="flex-1 h-2 bg-muted rounded-full">
        <div
          className="h-2 rounded-full transition-all"
          style={{
            width:      `${Math.round(entry.score * 100)}%`,
            background: getBarColor(entry.score),
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
    <div className="glass border border-border rounded-2xl p-5">
      <p className="text-xs text-muted-foreground mb-4">Hourly outlook</p>
      <div className="flex flex-col gap-3">
        {hourly.map((entry, index) => (
          <HourlyRow key={index} entry={entry} />
        ))}
      </div>
    </div>
  )
}

export default HourlyTimeline