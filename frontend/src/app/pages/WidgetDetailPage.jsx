import { useParams, useNavigate, useLocation } from '../router-compat'
import Navbar from '../components/common/Navbar'
import { formatHourFr } from '../utils/time'
import {
  AreaChart, Area, XAxis, YAxis,
  Tooltip, ResponsiveContainer
} from 'recharts'

/*
  Config per widget id:
  - label and icon for the page header
  - color for the chart line and fill
  - formatValue: how to display Y axis values
  - formatTick: optional custom Y axis tick
*/
const WIDGET_CONFIG = {
  humidity: {
    label: 'Humidity', icon: '💧',
    color: '#5cbdb9',
    formatValue: v => `${Math.round(v)}%`,
    unit: '%',
  },
  feels_like: {
    label: 'Feels like', icon: '🌡',
    color: '#f97316',
    formatValue: v => `${v.toFixed(1)}°C`,
    unit: '°C',
  },
  wind: {
    label: 'Wind', icon: '💨',
    color: '#7aa8e6',
    formatValue: v => `${v.toFixed(1)} m/s`,
    unit: 'm/s',
  },
  uv_index: {
    label: 'UV index', icon: '🔆',
    color: '#fbbf24',
    formatValue: v => `${v.toFixed(1)}`,
    unit: '',
  },
  visibility: {
    label: 'Visibility', icon: '👁',
    color: '#34d399',
    formatValue: v => `${v.toFixed(1)} km`,
    unit: 'km',
  },
  pressure: {
    label: 'Pressure', icon: '⬇',
    color: '#5cbdb9',
    formatValue: v => `${Math.round(v)} hPa`,
    unit: 'hPa',
  },
}

/*
  Formats ISO time string to a short hour label for the X axis.
  "2026-10-22T14:00:00+00:00" → "14:00"
*/
// function formatHour(isoString) {
//   const match = isoString.match(/[T ](\d{2}):(\d{2})/);

//   if (!match) return '';

//   return `${match[1]}:${match[2]}`;
  
  // const date = new Date(isoString)
  // return date.toLocaleTimeString('fr-FR', {
  //   hour: '2-digit',
  //   minute: '2-digit',
  //   timeZone: 'Europe/Paris',
  // })
// }

function WidgetDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()

  /*
    Retrieve widgets from router state — same pattern as ActivityPage.
    The widgets object was passed when the user clicked a widget card.
  */
  const widgets = location.state?.widgets
  const widgetData = widgets?.[id]
  const config = WIDGET_CONFIG[id]

  if (!widgetData || !config) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <div className="text-center py-20 text-muted-foreground text-sm">
          Widget not found.{' '}
          <button onClick={() => navigate(-1)} className="text-primary">
            Go back
          </button>
        </div>
      </div>
    )
  }

  /*
    Transform hourly_values into the shape Recharts expects.
    We add a formatted hour label for the X axis.
  */
  const chartData = widgetData.hourly_values.map(entry => ({
    time: entry.time_step_fr,
    hour:  formatHourFr(entry.time_step_fr),
    value: entry.value,
  }))

  return (
    <div className="min-h-screen">
      <Navbar />

      <div className="max-w-5xl mx-auto px-6 py-10 animate-rise">

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-muted-foreground hover:text-primary transition-colors inline-flex items-center gap-1 rounded-full border border-border px-3 py-1.5 glass"
          >
            ← Back
          </button>
          <h1 className="text-2xl sm:text-3xl font-semibold text-foreground">
            {config.icon} {config.label}
          </h1>
        </div>

        {/* Current value summary */}
        <div className="glass border border-border rounded-2xl p-5 mb-4 flex items-baseline gap-3">
          <span className="text-4xl font-medium text-foreground">
            {widgetData.value}
          </span>
          <span className="text-lg text-muted-foreground">{widgetData.unit}</span>
          <span className="text-sm text-muted-foreground ml-2">— {widgetData.message}</span>
        </div>

        {/* Hourly chart */}
        <div className="glass border border-border rounded-2xl p-5 mb-4">
          <p className="text-xs text-muted-foreground mb-4">Hourly forecast</p>

          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id={`grad-${id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={config.color} stopOpacity={0.15} />
                  <stop offset="100%" stopColor={config.color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="time"
                tickFormatter={value => formatHourFr(value)}
                tick={{ fontSize: 10, fill: '#8fb3c4' }}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
                // dataKey="hour"
                // tick={{ fontSize: 10, fill: '#8fb3c4' }}
                // tickLine={false}
                // axisLine={false}
                // interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#8fb3c4' }}
                tickLine={false}
                axisLine={false}
                width={40}
                tickFormatter={v => `${v.toFixed(0)}${config.unit}`}
              />
              <Tooltip
                labelFormatter={value => {
                const date = new Date(value)

                return date.toLocaleString('fr-FR', {
                  weekday: 'short',
                  day: '2-digit',
                  month: 'short',
                  hour: '2-digit',
                  minute: '2-digit',
                  timeZone: 'Europe/Paris',
                })
              }}
                formatter={v => [config.formatValue(v), config.label]}
                contentStyle={{
                  border: '0.5px solid #24456a',
                  borderRadius: '8px',
                  fontSize: 12,
                }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke={config.color}
                strokeWidth={2}
                fill={`url(#grad-${id})`}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Variable description box */}
        <div className="glass border border-border rounded-2xl p-5 bg-muted">
          <p className="text-xs text-muted-foreground mb-2">About this variable</p>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {widgetData.variable_description}
          </p>
        </div>

      </div>
    </div>
  )
}

export default WidgetDetailPage