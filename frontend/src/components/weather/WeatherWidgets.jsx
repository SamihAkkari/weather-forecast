import { useNavigate } from 'react-router-dom'

/*
  We add useNavigate here so each widget card navigates
  to its detail page when clicked.
  The full widgets object is passed via router state so
  WidgetDetailPage can find the right widget by id
  without a separate API call — same pattern as activities.
*/

function ProgressBar({ percent, color }) {
  return (
    <div className="w-full bg-gray-100 rounded-full h-1 mb-3">
      <div
        className="h-1 rounded-full transition-all"
        style={{
          width: `${Math.min(100, Math.max(0, percent))}%`,
          background: color
        }}
      />
    </div>
  )
}

function WindCompass({ direction }) {
  const angles = {
    N: 0, NE: 45, E: 90, SE: 135,
    S: 180, SW: 225, W: 270, NW: 315
  }
  const angle = angles[direction] ?? 0
  return (
    <div className="flex items-center justify-center mb-3">
      <div className="w-8 h-8 rounded-full border border-gray-200 flex items-center justify-center">
        <div style={{
          width: 2, height: 12, background: '#378ADD',
          borderRadius: 2,
          transform: `rotate(${angle}deg)`,
          transformOrigin: 'center center',
        }} />
      </div>
    </div>
  )
}

function SunArc({ progress }) {
  const r = 28, cx = 40, cy = 38
  const angle = Math.PI + progress * (0 - Math.PI)
  const dotX = cx + r * Math.cos(angle)
  const dotY = cy + r * Math.sin(angle)
  return (
    <div className="flex justify-center mb-2">
      <svg width="80" height="42" viewBox="0 0 80 42">
        <path d={`M ${cx-r} ${cy} A ${r} ${r} 0 0 1 ${cx+r} ${cy}`}
          fill="none" stroke="#f3f4f6" strokeWidth="3" strokeLinecap="round"/>
        <path d={`M ${cx-r} ${cy} A ${r} ${r} 0 0 1 ${dotX} ${dotY}`}
          fill="none" stroke="#fbbf24" strokeWidth="3" strokeLinecap="round"/>
        <circle cx={dotX} cy={dotY} r="4" fill="#fbbf24" />
      </svg>
    </div>
  )
}

function UvBar({ value }) {
  const max = 11
  const percent = (value / max) * 100
  const color =
    value <= 2  ? '#4ade80' :
    value <= 5  ? '#fbbf24' :
    value <= 7  ? '#f97316' :
    value <= 10 ? '#ef4444' : '#9333ea'
  return <ProgressBar percent={percent} color={color} />
}

/*
  Widget now accepts an onClick prop and shows a small
  arrow indicator in the top right corner.
*/
function Widget({ label, icon, value, unit, message, visual, onClick }) {
  return (
    <div
      onClick={onClick}
      className="border border-gray-100 rounded-xl p-4 bg-white cursor-pointer hover:border-gray-300 transition-colors relative group"
    >
      {/*
        Small arrow indicator — visible on hover.
        Tells the user the card is clickable without being intrusive.
      */}
      <span className="absolute top-3 right-3 text-xs text-gray-300 group-hover:text-gray-400 transition-colors">
        ↗
      </span>

      <p className="text-xs text-gray-400 mb-3">{icon} {label}</p>
      <p className="text-2xl font-medium text-gray-900 mb-3">
        {value}<span className="text-base font-normal text-gray-400 ml-0.5">{unit}</span>
      </p>
      {visual}
      <p className="text-xs text-gray-400 leading-relaxed">{message}</p>
    </div>
  )
}

function WeatherWidgets({ widgets }) {
  const navigate = useNavigate()

  function parseSunProgress(sunriseStr, messageStr) {
    try {
      const now = new Date()
      const [rH, rM] = sunriseStr.split(':').map(Number)
      const sunsetMatch = messageStr.match(/(\d{2}):(\d{2})/)
      if (!sunsetMatch) return 0.5
      const [sH, sM] = [parseInt(sunsetMatch[1]), parseInt(sunsetMatch[2])]
      const riseMinutes = rH * 60 + rM
      const setMinutes  = sH * 60 + sM
      const nowMinutes  = now.getHours() * 60 + now.getMinutes()
      return Math.min(1, Math.max(0, (nowMinutes - riseMinutes) / (setMinutes - riseMinutes)))
    } catch { return 0.5 }
  }

  // const { humidity, feels_like, wind, sunrise, uv_index, visibility, pressure } = widgets
  const { humidity, feels_like, wind, sunrise, pressure } = widgets
  const sunProgress = parseSunProgress(sunrise.value, sunrise.message)

  /*
    handleWidgetClick navigates to /widget/:id and passes
    the full widgets object in router state.
    The detail page finds the right widget by id from state.
    sunrise is excluded since it has no hourly forecast values
    that make sense to chart.
  */
  function handleWidgetClick(id) {
    navigate(`/widget/${id}`, { state: { widgets } })
  }

  return (
    <div>
      <p className="text-xs text-gray-400 mb-2">Weather details</p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">

        <Widget
          label="Humidity" icon="💧"
          value={humidity.value} unit={humidity.unit}
          message={humidity.message}
          visual={<ProgressBar percent={humidity.value} color="#60a5fa" />}
          onClick={() => handleWidgetClick('humidity')}
        />

        <Widget
          label="Feels like" icon="🌡"
          value={feels_like.value} unit={feels_like.unit}
          message={feels_like.message}
          visual={<ProgressBar percent={((feels_like.value + 20) / 60) * 100} color="#f97316" />}
          onClick={() => handleWidgetClick('feels_like')}
        />

        <Widget
          label="Wind" icon="💨"
          value={wind.value} unit={wind.unit}
          message={wind.message}
          visual={<WindCompass direction={wind.direction} />}
          onClick={() => handleWidgetClick('wind')}
        />

        {/*
          Sunrise widget is NOT clickable — no hourly data to show.
          No onClick passed, no ↗ arrow rendered.
        */}
        <Widget
          label="Sunrise" icon="🌅"
          value={sunrise.value} unit=""
          message={sunrise.message}
          visual={<SunArc progress={sunProgress} />}
        />

        {/* <Widget
          label="UV index" icon="🔆"
          value={uv_index.value} unit=""
          message={uv_index.message}
          visual={<UvBar value={uv_index.value} />}
          onClick={() => handleWidgetClick('uv_index')}
        />

        <Widget
          label="Visibility" icon="👁"
          value={visibility.value} unit={visibility.unit}
          message={visibility.message}
          visual={<ProgressBar percent={(visibility.value / 10) * 100} color="#60a5fa" />}
          onClick={() => handleWidgetClick('visibility')}
        /> */}

        <Widget
          label="Pressure" icon="⬇"
          value={pressure.value} unit={pressure.unit}
          message={pressure.message}
          visual={<ProgressBar percent={((pressure.value - 970) / 60) * 100} color="#a78bfa" />}
          onClick={() => handleWidgetClick('pressure')}
        />

      </div>
    </div>
  )
}

export default WeatherWidgets