import {
  AreaChart, Area, XAxis, YAxis,
  Tooltip, ResponsiveContainer
} from 'recharts'

/*
  Converts the degradation dict {1: 0.52, 2: 0.58, ...}
  into a sorted array Recharts can consume.
*/
function buildChartData(degradation) {
  return Object.entries(degradation)
    .map(([step, mae]) => ({
      step:  parseInt(step),
      mae:   mae,
    }))
    .sort((a, b) => a.step - b.step)
}

function DegradationChart({ degradation, color, unit }) {
  const data = buildChartData(degradation)

  return (
    <ResponsiveContainer width="100%" height={180}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id={`grad-${color.replace('#','')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor={color} stopOpacity={0.15} />
            <stop offset="100%" stopColor={color} stopOpacity={0}    />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="step"
          tick={{ fontSize: 10, fill: '#9ca3af' }}
          tickLine={false}
          axisLine={false}
          label={{
            value: 'Forecast horizon (h)',
            position: 'insideBottom',
            offset: -2,
            fontSize: 10,
            fill: '#d1d5db',
          }}
          height={32}
        />
        <YAxis
          tick={{ fontSize: 10, fill: '#9ca3af' }}
          tickLine={false}
          axisLine={false}
          width={36}
          tickFormatter={v => `${v.toFixed(1)}`}
        />
        <Tooltip
          formatter={v => [`${v.toFixed(2)} ${unit}`, 'MAE']}
          labelFormatter={step => `Horizon +${step}h`}
          contentStyle={{
            border: '0.5px solid #f0f0f0',
            borderRadius: '8px',
            fontSize: 12,
          }}
        />
        <Area
          type="monotone"
          dataKey="mae"
          stroke={color}
          strokeWidth={2}
          fill={`url(#grad-${color.replace('#','')})`}
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export default DegradationChart