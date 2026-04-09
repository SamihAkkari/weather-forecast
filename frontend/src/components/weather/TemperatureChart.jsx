import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts'

function formatHour(timeString) {
  const date = new Date(timeString)
  return `${date.getHours()}:00`
}

function TemperatureChart({ forecast }) {
  const data = forecast.map(entry => ({
    hour: formatHour(entry.time_step_fr),
    temperature: entry.temperature_celsius,
  }))

  return (
    <div className="border border-gray-100 rounded-xl p-5 mb-6">
      <p className="text-xs text-gray-400 mb-4">Temperature — next 48h</p>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <XAxis
            dataKey="hour"
            tick={{ fontSize: 11, fill: '#9ca3af' }}
            tickLine={false}
            axisLine={false}
            interval={3}
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#9ca3af' }}
            tickLine={false}
            axisLine={false}
            unit="°C"
            width={30}
          />
          <Tooltip
            formatter={(value) => [`${value}°C`, 'Temperature']}
            labelStyle={{ fontSize: 12, color: '#6b7280' }}
            contentStyle={{
              border: '0.5px solid #f0f0f0',
              borderRadius: '8px',
              fontSize: 12,
            }}
          />
          <Area
            type="monotone"
            dataKey="temperature" // Selects the temperature as the data to plot
            stroke="#378ADD"
            strokeWidth={2}
            fill="#378ADD"
            fillOpacity={0.07}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default TemperatureChart