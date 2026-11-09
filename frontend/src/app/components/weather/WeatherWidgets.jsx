import { useNavigate } from '../../router-compat'

/*
  We add useNavigate here so each widget card navigates
  to its detail page when clicked.
  The full widgets object is passed via router state so
  WidgetDetailPage can find the right widget by id
  without a separate API call   same pattern as activities.
*/

function ProgressBar({ percent, color }) {
  return (
    <div className="w-full bg-muted rounded-full h-1 mb-3">
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
      <div className="w-8 h-8 rounded-full border border-border flex items-center justify-center">
        <div style={{
          width: 2, height: 12, background: '#5cbdb9',
          borderRadius: 2,
          transform: `rotate(${angle}deg)`,
          transformOrigin: 'center center',
        }} />
      </div>
    </div>
  )
}

function Widget({ label, icon, value, unit, message, visual, onClick }) {
  return (
    <div
      onClick={onClick}
      className="glass border border-border rounded-2xl p-4 glass cursor-pointer lift transition-colors relative group"
    >
      {/*
        Small arrow indicator   visible on hover.
        Tells the user the card is clickable without being intrusive.
      */}
      <span className="absolute top-3 right-3 text-xs text-subtle group-hover:text-primary transition-colors inline-flex items-center gap-1 rounded-full border border-border px-3 py-1.5 glass">
        ↗
      </span>

      <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-primary mb-4">{icon} {label}</p>
      <p className="text-2xl font-medium text-foreground mb-3">
        {value}<span className="text-base font-normal text-muted-foreground ml-0.5">{unit}</span>
      </p>
      {visual}
      <p className="text-xs text-muted-foreground leading-relaxed">{message}</p>
    </div>
  )
}

function WeatherWidgets({ widgets }) {
  const navigate = useNavigate()

  const { humidity, feels_like, wind, pressure } = widgets

  function handleWidgetClick(id) {
    navigate(`/widget/${id}`, { state: { widgets } })
  }

  return (
    <div>
      <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-primary mb-4">Weather details</p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">

        <Widget
          label="Humidity" icon="💧"
          value={humidity.value} unit={humidity.unit}
          message={humidity.message}
          visual={<ProgressBar percent={humidity.value} color="#5cbdb9" />}
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

        <Widget
          label="Pressure" icon="⬇"
          value={pressure.value} unit={pressure.unit}
          message={pressure.message}
          visual={<ProgressBar percent={((pressure.value - 970) / 60) * 100} color="#7aa8e6" />}
          onClick={() => handleWidgetClick('pressure')}
        />

      </div>
    </div>
  )
}

export default WeatherWidgets