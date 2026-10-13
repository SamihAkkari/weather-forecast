import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts'

function TemperatureAnalysis({ data }) {
  /*
    data.degradation is an object like { 1: 0.31, 2: 0.38, ... }
    Recharts needs an array of objects, so we convert it here.
    Object.entries gives us [["1", 0.31], ["2", 0.38], ...]
    We sort by horizon to guarantee the X axis is in order.
  */
  const chartData = Object.entries(data.degradation)
    .map(([horizon, mae]) => ({
      horizon: `+${horizon}h`,
      mae: Math.round(mae * 100) / 100
    }))
    .sort((a, b) => {
      const aNum = parseInt(a.horizon)
      const bNum = parseInt(b.horizon)
      return aNum - bNum
    })

  /*
    We compute a simple insight from the data directly.
    First and last values give us the error at shortest and longest horizon.
  */
  const first = chartData[0]
  const last = chartData[chartData.length - 1]
  const insight = `Temperature MAE grows from ${first.mae}°C at ${first.horizon} to ${last.mae}°C at ${last.horizon} — averaged across all selected runs.`

  return (
    <div className="border border-gray-100 rounded-xl p-5">
      <p className="text-xs text-gray-400 mb-4">
        Temperature — mean absolute error by forecast horizon
      </p>

      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={chartData}>
          <XAxis
            dataKey="horizon"
            tick={{ fontSize: 10, fill: '#9ca3af' }}
            tickLine={false}
            axisLine={false}
            interval={5}
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
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>

      <div className="mt-4 px-3 py-2.5 bg-blue-50 rounded-lg">
        <p className="text-xs text-blue-700">💡 {insight}</p>
      </div>
    </div>
  )
}

export default TemperatureAnalysis