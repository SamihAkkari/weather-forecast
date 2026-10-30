import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import Navbar from '../components/common/Navbar'
import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Legend
} from 'recharts'
import { usePvProduction } from '../hooks/usePvProduction'
import { formatHourFr } from '../utils/time'

/*
  Formats ISO time string to hour label.
  "2026-10-22T13:00:00" → "13:00"
*/
// function formatHour(isoString) {
//   const date = new Date(isoString)
//   return `${String(date.getUTCHours()).padStart(2, '0')}:${String(date.getUTCMinutes()).padStart(2, '0')}`
//   // return date.toLocaleTimeString('fr-FR', {
//   //   hour: '2-digit',
//   //   minute: '2-digit',
//   //   timeZone: 'Europe/Paris',
//   // })
// }

/*
  Generates a human-readable insight sentence from total energy.
  Uses simple fixed equivalences — easy to extend later.
*/
// function buildInsight(total_kwh, capacity_kw) {
//   const washingMachine = (total_kwh / 0.5).toFixed(0)  // ~0.5 kWh per cycle
//   const evKm           = (total_kwh * 6).toFixed(0)     // ~6 km per kWh (average EV)
//   const fridgeHours    = (total_kwh / 0.04).toFixed(0)  // ~40W fridge

//   return `Your ${capacity_kw} kWp system will produce ${total_kwh} kWh over the forecast period — 
// enough to run a washing machine ${washingMachine} times, 
// cover approximately ${evKm} km of EV driving, 
// or power a fridge for ${fridgeHours} hours.`
// }

/*
  InputField — reusable labelled input used in the form.
*/
function InputField({ label, hint, value, onChange, min, max, step }) {
  return (
    <div>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <input
        type="number"
        value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        min={min}
        max={max}
        step={step ?? 0.1}
        className="w-full border border-gray-100 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:border-gray-300"
      />
      {hint && <p className="text-xs text-gray-300 mt-1">{hint}</p>}
    </div>
  )
}

/*
  SummaryCard — one of the three metric cards at the top of results.
*/
function SummaryCard({ label, value, unit, sub }) {
  return (
    <div className="border border-gray-100 rounded-xl p-4">
      <p className="text-xs text-gray-400 mb-2">{label}</p>
      <p className="text-2xl font-medium text-gray-900 mb-1">
        {value}
        <span className="text-sm font-normal text-gray-400 ml-1">{unit}</span>
      </p>
      <p className="text-xs text-gray-400">{sub}</p>
    </div>
  )
}

function PvProductionPage({ selectedLocation }) {
  const navigate  = useNavigate()
  const location  = useLocation()
  const { pvData, loading, error, compute } = usePvProduction()

  /*
    Location comes either from App.jsx prop (navigated via entry card)
    or from router state as fallback.
  */
  const loc = selectedLocation ?? location.state?.location

  /*
    System specification state — default values are sensible
    starting points for a residential installation in France.
    Tilt 30° and azimuth 180° (south-facing) are optimal for France.
  */
  const [system, setSystem] = useState({
    capacity_kw:          3.0,
    tilt:                 30,
    azimuth:              180,
    losses_pct:           14.0,
    inverter_capacity_kw: 2.5,
  })

  function handleChange(field, value) {
    setSystem(prev => ({ ...prev, [field]: value }))
  }

  function handleCompute() {
    if (!loc) return
    compute(loc, system)
  }

  /*
    Prepare chart data from hourly array.
    power_kw is derived from power_w for cleaner axis labels.
  */
  const chartData = pvData?.hourly.map(entry => ({
    hour:      formatHourFr(entry.time),
    power_kw:  parseFloat((entry.power_w / 1000).toFixed(2)),
    clipping_pct: entry.clipping_percentage,
    ghi_wm2:   entry.ghi_wm2,
    poa_wm2:   entry.poa_wm2,
  })) ?? []

  /*
    Derived summary values computed from the response.
    peak_pct: how close the peak got to the inverter limit (clipping indicator)
    efficiency: ratio of actual output to theoretical max (capacity * hours)
  */
  const peakKw     = pvData ? (pvData.peak_power_w / 1000).toFixed(2)  : null
  const peakHour   = pvData ? formatHourFr(pvData.peak_hour)              : null
  const peakPct    = pvData
    ? Math.round((pvData.peak_power_w / (system.inverter_capacity_kw * 1000)) * 100)
    : null
  const inverterLimitKw = system.inverter_capacity_kw

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
            ☀️ PV Production Forecast
          </h1>
        </div>

        {/* Location indicator */}
        {loc ? (
          <div className="text-xs text-gray-400 mb-6">
            📍 {loc.lat.toFixed(4)}, {loc.lng.toFixed(4)}
          </div>
        ) : (
          <div className="text-sm text-red-400 mb-6">
            No location selected — please go back and click a location on the map.
          </div>
        )}

        {/* System specification form */}
        <div className="border border-gray-100 rounded-xl p-5 mb-6">
          <p className="text-xs text-gray-400 mb-4">System specifications</p>

          <div className="grid grid-cols-2 gap-4 mb-4 sm:grid-cols-3">
            <InputField
              label="Capacity (kWp)"
              hint="Total installed DC capacity"
              value={system.capacity_kw}
              onChange={v => handleChange('capacity_kw', v)}
              min={0.1} max={100} step={0.1}
            />
            <InputField
              label="Tilt (°)"
              hint="0 = flat, 90 = vertical"
              value={system.tilt}
              onChange={v => handleChange('tilt', v)}
              min={0} max={90} step={1}
            />
            <InputField
              label="Azimuth (°)"
              hint="180 = south-facing"
              value={system.azimuth}
              onChange={v => handleChange('azimuth', v)}
              min={0} max={360} step={1}
            />
            <InputField
              label="Inverter capacity (kW)"
              hint="AC output limit"
              value={system.inverter_capacity_kw}
              onChange={v => handleChange('inverter_capacity_kw', v)}
              min={0.1} max={100} step={0.1}
            />
            <InputField
              label="Losses (%)"
              hint="Wiring, soiling, shading"
              value={system.losses_pct}
              onChange={v => handleChange('losses_pct', v)}
              min={0} max={50} step={0.5}
            />
          </div>

        <button
            type="button"
            onClick={handleCompute}
            disabled={!loc || loading}
            className="
                flex w-full min-h-[52px] items-center justify-center gap-2
                rounded-xl bg-blue-400 px-6 py-3
                text-base font-semibold text-white
                shadow-lg shadow-blue-600/20
                transition-all duration-200
                hover:bg-grey-700 hover:shadow-xl
                active:scale-[0.98]
                disabled:cursor-not-allowed
                disabled:bg-gray-400 disabled:opacity-70
                disabled:shadow-none
                focus-visible:outline-none
                focus-visible:ring-4 focus-visible:ring-blue-300
            "
            >
            {loading ? (
                <>
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Computing...
                </>
            ) : (
                <>
                <span>⚡</span>
                Compute Production
                <span aria-hidden="true">→</span>
                </>
            )}
            </button>

          {/* <button
            onClick={handleCompute}
            disabled={!loc || loading}
            className="w-full py-2 bg-gray-900 text-grey text-sm rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? 'Computing...' : 'Compute production'}
          </button> */}
        </div>

        {/* Error state */}
        {error && !loading && (
          <div className="text-center py-12 text-red-400 text-sm mb-6">
            {error}
          </div>
        )}

        {/* Results */}
        {pvData && !loading && (
          <div className="space-y-4">

            {/* Summary cards */}
            <div className="grid grid-cols-3 gap-3">
              <SummaryCard
                label="Total energy"
                value={pvData.total_energy_kwh}
                unit="kWh"
                sub={pvData.energy_period_message}
              />
              <SummaryCard
                label="Peak output"
                value={peakKw}
                unit="kW"
                sub={`at ${peakHour}`}
              />
              <SummaryCard
                label="Clipping"
                value={pvData.energy_clipping_percent}
                unit="%"
                sub={pvData.clipping_message}
              />
            </div>

            {/* Insight box */}
            <div className="bg-green-50 rounded-xl p-4">
              <p className="text-xs text-green-700 leading-relaxed">
                💡 {pvData.insight_message}
              </p>
            </div>

            {/* Power output chart */}
            <div className="border border-gray-100 rounded-xl p-5">
              <p className="text-xs text-gray-400 mb-1">Hourly AC power output</p>
              <p className="text-xs text-gray-300 mb-4">
                Dashed line shows inverter capacity limit ({inverterLimitKw} kW)
              </p>

              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="pvGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.2} />
                      <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="hour"
                    tick={{ fontSize: 10, fill: '#9ca3af' }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: '#9ca3af' }}
                    tickLine={false}
                    axisLine={false}
                    unit=" kW"
                    width={40}
                  />
                  <Tooltip
                    content={({ active, payload, label }) => {
                        if (active && payload?.length) {
                        const data = payload[0].payload

                        return (
                            <div className="bg-white border border-gray-100 rounded-lg p-3 text-xs shadow-sm">
                            <p className="text-gray-400 mb-2">{label}</p>
                            <p className="text-amber-500">
                                AC Power: {data.power_kw} kW
                            </p>
                            <p className="text-blue-500">
                                Clipping: {data.clipping_pct}%
                            </p>
                            </div>
                        )
                        }
                        return null
                    }}
                    // formatter={v => [`${v} kW`, 'AC Power']}
                    // labelFormatter={label => `Hour: ${label}`}
                    // contentStyle={{
                    //   border: '0.5px solid #f0f0f0',
                    //   borderRadius: '8px',
                    //   fontSize: 12,
                    // }}
                  />
                  {/*
                    ReferenceLine shows the inverter capacity limit.
                    If the power curve touches this line the system is clipping
                    — the inverter is rejecting excess DC power from the panels.
                  */}
                  <ReferenceLine
                    y={inverterLimitKw}
                    stroke="#e5e7eb"
                    strokeDasharray="4 3"
                    label={{
                      value: `${inverterLimitKw} kW limit`,
                      position: 'insideTopLeft',
                      fontSize: 10,
                      fill: '#d1d5db',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="power_kw"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    fill="url(#pvGrad)"
                    dot={{ r: 3, fill: '#f59e0b', strokeWidth: 0 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Irradiance chart */}
            <div className="border border-gray-100 rounded-xl p-5">
              <p className="text-xs text-gray-400 mb-1">
                Irradiance — GHI vs POA (W/m²)
              </p>
              <p className="text-xs text-gray-300 mb-4">
                POA is the irradiance hitting your tilted panels —
                higher than GHI when panels face the sun optimally
              </p>

              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={chartData}>
                  <XAxis
                    dataKey="hour"
                    tick={{ fontSize: 10, fill: '#9ca3af' }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: '#9ca3af' }}
                    tickLine={false}
                    axisLine={false}
                    unit=" W/m²"
                    width={52}
                  />
                  <Tooltip
                    formatter={(v, name) => [
                      `${v} W/m²`,
                      name === 'ghi_wm2' ? 'GHI (horizontal)' : 'POA (panel surface)'
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
                    formatter={v => v === 'ghi_wm2' ? 'GHI' : 'POA'}
                    wrapperStyle={{ fontSize: 11, color: '#9ca3af' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="ghi_wm2"
                    stroke="#60a5fa"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="poa_wm2"
                    stroke="#f97316"
                    strokeWidth={1.5}
                    strokeDasharray="4 2"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

          </div>
        )}

      </div>
    </div>
  )
}

export default PvProductionPage