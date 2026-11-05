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
    <div className="glass border border-border rounded-2xl p-5 mb-6">
      <p className="text-xs text-muted-foreground mb-4">Temperature   next 48h</p>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <XAxis
            dataKey="hour"
            tick={{ fontSize: 11, fill: '#8fb3c4' }}
            tickLine={false}
            axisLine={false}
            interval={3}
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#8fb3c4' }}
            tickLine={false}
            axisLine={false}
            unit="°C"
            width={30}
          />
          <Tooltip
            formatter={(value) => [`${value}°C`, 'Temperature']}
            labelStyle={{ fontSize: 12, color: '#8fb3c4' }}
            contentStyle={{
              border: '0.5px solid #24456a',
              borderRadius: '8px',
              fontSize: 12,
            }}
          />
          <Area
            type="monotone"
            dataKey="temperature" // Selects the temperature as the data to plot
            stroke="#5cbdb9"
            strokeWidth={2}
            fill="#5cbdb9"
            fillOpacity={0.07}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default TemperatureChart