import { useParams, useNavigate, useLocation } from 'react-router-dom'
import Navbar from '../components/common/Navbar'
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
    color: '#60a5fa',
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
    color: '#a78bfa',
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
    color: '#818cf8',
    formatValue: v => `${Math.round(v)} hPa`,
    unit: 'hPa',
  },
}

/*
  Formats ISO time string to a short hour label for the X axis.
  "2026-10-22T14:00:00+00:00" → "14:00"
*/
function formatHour(isoString) {
  const match = isoString.match(/[T ](\d{2}):(\d{2})/);

  if (!match) return '';

  return `${match[1]}:${match[2]}`;
  
  // const date = new Date(isoString)
  // return date.toLocaleTimeString('fr-FR', {
  //   hour: '2-digit',
  //   minute: '2-digit',
  //   timeZone: 'Europe/Paris',
  // })
}

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
      <div className="min-h-screen bg-white">
        <Navbar />
        <div className="text-center py-20 text-gray-400 text-sm">
          Widget not found.{' '}
          <button onClick={() => navigate(-1)} className="text-blue-500">
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
    hour:  formatHour(entry.time_step_fr),
    value: entry.value,
  }))

  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      <div className="max-w-3xl mx-auto px-8 py-8">

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
          >
            ← Back
          </button>
          <h1 className="text-lg font-medium text-gray-900">
            {config.icon} {config.label}
          </h1>
        </div>

        {/* Current value summary */}
        <div className="border border-gray-100 rounded-xl p-5 mb-4 flex items-baseline gap-3">
          <span className="text-4xl font-medium text-gray-900">
            {widgetData.value}
          </span>
          <span className="text-lg text-gray-400">{widgetData.unit}</span>
          <span className="text-sm text-gray-400 ml-2">— {widgetData.message}</span>
        </div>

        {/* Hourly chart */}
        <div className="border border-gray-100 rounded-xl p-5 mb-4">
          <p className="text-xs text-gray-400 mb-4">Hourly forecast</p>

          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id={`grad-${id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={config.color} stopOpacity={0.15} />
                  <stop offset="100%" stopColor={config.color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="hour"
                tick={{ fontSize: 10, fill: '#9ca3af' }}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#9ca3af' }}
                tickLine={false}
                axisLine={false}
                width={40}
                tickFormatter={v => `${v.toFixed(0)}${config.unit}`}
              />
              <Tooltip
                formatter={v => [config.formatValue(v), config.label]}
                contentStyle={{
                  border: '0.5px solid #f0f0f0',
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
        <div className="border border-gray-100 rounded-xl p-5 bg-gray-50">
          <p className="text-xs text-gray-400 mb-2">About this variable</p>
          <p className="text-sm text-gray-600 leading-relaxed">
            {widgetData.variable_description}
          </p>
        </div>

      </div>
    </div>
  )
}

export default WidgetDetailPage