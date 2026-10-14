/*
  WeatherWidgets renders a grid of weather detail cards.
  Each card has:
  - A label and icon at the top
  - A large value
  - A visual bar showing the value relative to its scale
  - An insight message at the bottom

  We define one generic Widget component and configure each
  weather criteria through a config object. This avoids
  building seven nearly identical components.
*/

/*
  ProgressBar renders a thin colored bar filled to a given percentage.
  percent: 0 to 100
  color: any valid CSS color
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

/*
  WindCompass renders a small circle with a directional arrow
  showing which way the wind is blowing.
  direction: one of "N", "NE", "E", "SE", "S", "SW", "W", "NW"
*/
function WindCompass({ direction }) {
  const angles = {
    N: 0, NE: 45, E: 90, SE: 135,
    S: 180, SW: 225, W: 270, NW: 315
  }
  const angle = angles[direction] ?? 0

  return (
    <div className="flex items-center justify-center mb-3">
      <div
        className="w-8 h-8 rounded-full border border-gray-200 flex items-center justify-center"
        style={{ position: 'relative' }}
      >
        <div
          style={{
            width: 2,
            height: 12,
            background: '#378ADD',
            borderRadius: 2,
            transform: `rotate(${angle}deg)`,
            transformOrigin: 'center center',
          }}
        />
      </div>
    </div>
  )
}

/*
  SunArc renders a simple semicircle showing how far through
  the day we are between sunrise and sunset.
  progress: 0 to 1 (where 0 = sunrise, 1 = sunset)
*/
function SunArc({ progress }) {
  const r = 28
  const cx = 40
  const cy = 38
  const startAngle = Math.PI
  const endAngle = 0
  const angle = startAngle + progress * (endAngle - startAngle)
  const dotX = cx + r * Math.cos(angle)
  const dotY = cy + r * Math.sin(angle)

  return (
    <div className="flex justify-center mb-2">
      <svg width="80" height="42" viewBox="0 0 80 42">
        {/* Arc track */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="#f3f4f6"
          strokeWidth="3"
          strokeLinecap="round"
        />
        {/* Arc progress */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${dotX} ${dotY}`}
          fill="none"
          stroke="#fbbf24"
          strokeWidth="3"
          strokeLinecap="round"
        />
        {/* Sun dot */}
        <circle cx={dotX} cy={dotY} r="4" fill="#fbbf24" />
      </svg>
    </div>
  )
}

/*
  Generic Widget component.
  label: string shown at top e.g. "Humidity"
  icon: emoji
  value: string or number to display large
  unit: string appended to value e.g. "%" or "km"
  message: insight sentence at bottom
  visual: a React element — ProgressBar, WindCompass, or SunArc
*/
function Widget({ label, icon, value, unit, message, visual }) {
  return (
    <div className="border border-gray-100 rounded-xl p-4 bg-white cursor-pointer hover:border-gray-300 transition-colors">
      <p className="text-xs text-gray-400 mb-3">
        {icon} {label}
      </p>
      <p className="text-2xl font-medium text-gray-900 mb-3">
        {value}<span className="text-base font-normal text-gray-400 ml-0.5">{unit}</span>
      </p>
      {visual}
      <p className="text-xs text-gray-400 leading-relaxed">{message}</p>
    </div>
  )
}

/*
  UvBar is a special progress bar with a color gradient
  that goes from green (low) to red (high) — standard UV index display.
*/
function UvBar({ value }) {
  const max = 11
  const percent = (value / max) * 100
  const color =
    value <= 2  ? '#4ade80' :
    value <= 5  ? '#fbbf24' :
    value <= 7  ? '#f97316' :
    value <= 10 ? '#ef4444' :
    '#9333ea'

  return <ProgressBar percent={percent} color={color} />
}

/*
  Main component — receives the widgets object from mockWeatherDetails.
  Renders a responsive grid of Widget cards.
*/
function WeatherWidgets({ widgets }) {
  const {
    humidity,
    feels_like,
    wind,
    sunrise,
    uv_index,
    visibility,
    pressure,
  } = widgets

  /*
    We compute a rough sun progress from the sunrise/sunset times.
    This tells the SunArc how far the sun has moved across the sky.
    In the real backend you'd pass this directly.
  */
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
      return Math.min(1, Math.max(0,
        (nowMinutes - riseMinutes) / (setMinutes - riseMinutes)
      ))
    } catch {
      return 0.5
    }
  }

  const sunProgress = parseSunProgress(sunrise.value, sunrise.message)

  return (
    <div>
      <p className="text-xs text-gray-400 mb-2">Weather details</p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">

        <Widget
          label="Humidity"
          icon="💧"
          value={humidity.value}
          unit={humidity.unit}
          message={humidity.message}
          visual={<ProgressBar percent={humidity.value} color="#60a5fa" />}
        />

        <Widget
          label="Feels like"
          icon="🌡"
          value={feels_like.value}
          unit={feels_like.unit}
          message={feels_like.message}
          visual={
            <ProgressBar
              percent={((feels_like.value + 20) / 60) * 100}
              color="#f97316"
            />
          }
        />

        <Widget
          label="Wind"
          icon="💨"
          value={wind.value}
          unit={wind.unit}
          message={wind.message}
          visual={<WindCompass direction={wind.direction} />}
        />

        <Widget
          label="Sunrise"
          icon="🌅"
          value={sunrise.value}
          unit=""
          message={sunrise.message}
          visual={<SunArc progress={sunProgress} />}
        />

        <Widget
          label="UV index"
          icon="🔆"
          value={uv_index.value}
          unit=""
          message={uv_index.message}
          visual={<UvBar value={uv_index.value} />}
        />

        <Widget
          label="Visibility"
          icon="👁"
          value={visibility.value}
          unit={visibility.unit}
          message={visibility.message}
          visual={
            <ProgressBar
              percent={(visibility.value / 10) * 100}
              color="#60a5fa"
            />
          }
        />

        <Widget
          label="Pressure"
          icon="⬇"
          value={pressure.value}
          unit={pressure.unit}
          message={pressure.message}
          visual={
            <ProgressBar
              percent={((pressure.value - 970) / 60) * 100}
              color="#a78bfa"
            />
          }
        />

      </div>
    </div>
  )
}

export default WeatherWidgets