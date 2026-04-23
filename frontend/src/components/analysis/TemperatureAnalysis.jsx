import { useState } from 'react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts'

/*
  Small helper that converts "2026-04-21T14:00:00" to "14:00".
  We use it to format the X axis labels on the chart.
*/
function formatHour(timeString) {
  const date = new Date(timeString)
  return `${date.getHours()}:00`
}

/*
  MetricCard is a tiny internal component used only inside this file.
  It renders a single grey box with a label and a value.
  We define it here rather than in components/common because it is
  specific to this analysis context and not reused anywhere else.
*/
function MetricCard({ label, value }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className="text-lg font-medium text-gray-900">{value}</p>
    </div>
  )
}

/*
  InsightBox renders the blue highlighted sentence at the bottom of each section.
  Again defined locally since it is only used in analysis components.
*/
function InsightBox({ text }) {
  return (
    <div className="mt-3 px-3 py-2.5 bg-blue-50 rounded-lg">
      <p className="text-xs text-blue-700">💡 {text}</p>
    </div>
  )
}

/*
  The main component receives the full temperature object from analysisData.
  It looks like:
  {
    comparison: [{time, forecast, observed}, ...],
    mae, rmse, bias,
    degradation: [{horizon_h, mae}, ...],
    insight: "..."
  }
*/
function TemperatureAnalysis({ data }) {
  /*
    activeView controls which chart is shown.
    It starts on 'comparison' and switches to 'degradation' when the user
    clicks the toggle button. We use useState because this is local UI state
    that only this component cares about — the parent page doesn't need to know.
  */
  const [activeView, setActiveView] = useState('comparison')

  /*
    We transform the comparison array once here so the chart receives
    clean data. formatHour converts the ISO string to a readable label.
  */
  const comparisonData = data.comparison.map(entry => ({
    hour: formatHour(entry.time),
    forecast: entry.forecast,
    observed: entry.observed,
  }))

  /*
    The degradation array already has the right shape for Recharts.
    We just rename horizon_h to "Horizon (h)" for the axis label.
  */
  const degradationData = data.degradation.map(entry => ({
    horizon: `+${entry.horizon_h}h`,
    mae: entry.mae,
  }))

  return (
    <div className="border border-gray-100 rounded-xl p-5">

      {/* Header row: title on the left, toggle buttons on the right */}
      <div className="flex justify-between items-center mb-4">
        <p className="text-xs text-gray-400">Temperature</p>

        {/*
          Toggle between two views.
          Each button checks if it is the active one and applies darker
          styling if so. This pattern avoids having two separate boolean states.
        */}
        <div className="flex border border-gray-100 rounded-lg overflow-hidden">
          <button
            onClick={() => setActiveView('comparison')}
            className={`text-xs px-3 py-1.5 transition-colors ${
              activeView === 'comparison'
                ? 'bg-gray-900 text-white'
                : 'bg-white text-gray-400 hover:text-gray-600'
            }`}
          >
            Forecast vs observed
          </button>
          <button
            onClick={() => setActiveView('degradation')}
            className={`text-xs px-3 py-1.5 transition-colors ${
              activeView === 'degradation'
                ? 'bg-gray-900 text-white'
                : 'bg-white text-gray-400 hover:text-gray-600'
            }`}
          >
            Error by horizon
          </button>
        </div>
      </div>

      {/*
        Conditional rendering based on activeView.
        Only one chart is shown at a time.
      */}

      {activeView === 'comparison' && (
        <div>
          {/*
            LineChart with two lines: one for forecast, one for observed.
            ResponsiveContainer makes the chart fill the parent width automatically.
            interval="preserveStartEnd" on XAxis shows only the first and last label
            plus a few in between, avoiding label crowding with 36 data points.
          */}
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={comparisonData}>
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
                unit="°"
                width={28}
              />
              <Tooltip
                formatter={(value, name) => [
                  `${value}°C`,
                  name === 'forecast' ? 'Forecast' : 'Observed'
                ]}
                contentStyle={{
                  border: '0.5px solid #f0f0f0',
                  borderRadius: '8px',
                  fontSize: 12,
                }}
              />
              <Legend
                iconType="line"
                iconSize={16}
                formatter={value => value === 'forecast' ? 'Forecast' : 'Observed'}
                wrapperStyle={{ fontSize: 11, color: '#9ca3af' }}
              />
              <Line
                type="monotone"
                dataKey="forecast"
                stroke="#378ADD"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="observed"
                stroke="#E24B4A"
                strokeWidth={1.5}
                strokeDasharray="4 2"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>

          {/* Three metric cards side by side */}
          <div className="grid grid-cols-3 gap-2 mt-4">
            <MetricCard label="MAE" value={`${data.mae}°C`} />
            <MetricCard label="RMSE" value={`${data.rmse}°C`} />
            <MetricCard label="Bias" value={`${data.bias > 0 ? '+' : ''}${data.bias}°C`} />
          </div>

          <InsightBox text={data.insight} />
        </div>
      )}

      {activeView === 'degradation' && (
        <div>
          {/*
            AreaChart showing how MAE grows with forecast horizon.
            A filled area makes the degradation trend more visually obvious
            than a plain line.
          */}
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={degradationData}>
              <XAxis
                dataKey="horizon"
                tick={{ fontSize: 10, fill: '#9ca3af' }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#9ca3af' }}
                tickLine={false}
                axisLine={false}
                unit="°"
                width={28}
              />
              <Tooltip
                formatter={value => [`${value}°C`, 'MAE']}
                contentStyle={{
                  border: '0.5px solid #f0f0f0',
                  borderRadius: '8px',
                  fontSize: 12,
                }}
              />
              <Area
                type="monotone"
                dataKey="mae"
                stroke="#378ADD"
                strokeWidth={2}
                fill="#378ADD"
                fillOpacity={0.07}
                dot={{ r: 3, fill: '#378ADD', strokeWidth: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>

          <p className="text-xs text-gray-300 mt-1 mb-3">MAE (°C) by forecast horizon</p>

          <InsightBox text={`Temperature error grows from ${degradationData[0].mae}°C at ${degradationData[0].horizon} to ${degradationData[degradationData.length - 1].mae}°C at ${degradationData[degradationData.length - 1].horizon} — typical for a deterministic NWP model.`} />
        </div>
      )}

    </div>
  )
}

export default TemperatureAnalysis