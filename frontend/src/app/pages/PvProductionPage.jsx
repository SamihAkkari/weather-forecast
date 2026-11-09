import { useState } from 'react'
import { useNavigate, useLocation } from '../router-compat'
import Navbar from '../components/common/Navbar'
import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Legend
} from 'recharts'
import { usePvProduction } from '../hooks/usePvProduction'
import { formatHourFr } from '../utils/time'

function InputField({ label, hint, value, onChange, min, max, step }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <input
        type="number"
        value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        min={min}
        max={max}
        step={step ?? 0.1}
        className="w-full border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary/40"
      />
      {hint && <p className="text-xs text-subtle mt-1">{hint}</p>}
    </div>
  )
}

function SummaryCard({ label, value, unit, sub }) {
  return (
    <div className="glass border border-border rounded-2xl p-4">
      <p className="text-xs text-muted-foreground mb-2">{label}</p>
      <p className="text-2xl font-medium text-foreground mb-1">
        {value}
        <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>
      </p>
      <p className="text-xs text-muted-foreground">{sub}</p>
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
    System specification state   default values are sensible
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
    time: entry.time,
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
            ☀️ PV Production Forecast
          </h1>
        </div>

        {/* Location indicator */}
        {loc ? (
          <div className="text-xs text-muted-foreground mb-6">
            📍 {loc.lat.toFixed(4)}, {loc.lng.toFixed(4)}
          </div>
        ) : (
          <div className="text-sm text-destructive mb-6">
            No location selected   please go back and click a location on the map.
          </div>
        )}

        {/* System specification form */}
        <div className="glass border border-border rounded-2xl p-5 mb-6">
          <p className="text-xs text-muted-foreground mb-4">System specifications</p>

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
                rounded-2xl bg-info px-6 py-3
                text-base font-semibold text-foreground
                shadow-lg shadow-blue-600/20
                transition-all duration-200
                hover:bg-grey-700 hover:shadow-xl
                active:scale-[0.98]
                disabled:cursor-not-allowed
                disabled:bg-secondary disabled:opacity-70
                disabled:shadow-none
                focus-visible:outline-none
                focus-visible:ring-4 focus-visible:ring-primary
            "
            >
            {loading ? (
                <>
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-foreground/30 border-t-white" />
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

        </div>

        {/* Error state */}
        {error && !loading && (
          <div className="text-center py-12 text-destructive text-sm mb-6">
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
            <div className="bg-success/15 rounded-2xl p-4">
              <p className="text-xs text-success leading-relaxed">
                💡 {pvData.insight_message}
              </p>
            </div>

            {/* Power output chart */}
            <div className="glass border border-border rounded-2xl p-5">
              <p className="text-xs text-muted-foreground mb-1">Hourly AC power output</p>
              <p className="text-xs text-subtle mb-4">
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
                    dataKey="time"
                    tickFormatter={value => formatHourFr(value)}
                    tick={{ fontSize: 10, fill: '#8fb3c4' }}
                    tickLine={false}
                    axisLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: '#8fb3c4' }}
                    tickLine={false}
                    axisLine={false}
                    unit=" kW"
                    width={40}
                  />
                  <Tooltip
                    content={({ active, payload, label }) => {
                        if (active && payload?.length) {
                        const data = payload[0].payload
                        const formattedDate = new Date(label).toLocaleString('fr-FR', {
                          weekday: 'short',
                          day: '2-digit',
                          month: 'short',
                          hour: '2-digit',
                          minute: '2-digit',
                          timeZone: 'Europe/Paris',
                        })                        

                        return (
                            <div className="glass border border-border rounded-lg p-3 text-xs shadow-sm">
                            <p className="text-muted-foreground mb-2">{formattedDate}</p>
                            <p className="text-warning">
                                AC Power: {data.power_kw} kW
                            </p>
                            <p className="text-primary">
                                Clipping: {data.clipping_pct}%
                            </p>
                            </div>
                        )
                        }
                        return null
                    }}
                  />
                  {/*
                    ReferenceLine shows the inverter capacity limit.
                    If the power curve touches this line the system is clipping
                      the inverter is rejecting excess DC power from the panels.
                  */}
                  <ReferenceLine
                    y={inverterLimitKw}
                    stroke="#24456a"
                    strokeDasharray="4 3"
                    label={{
                      value: `${inverterLimitKw} kW limit`,
                      position: 'insideTopLeft',
                      fontSize: 10,
                      fill: '#24456a',
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
            <div className="glass border border-border rounded-2xl p-5">
              <p className="text-xs text-muted-foreground mb-1">
                Irradiance   GHI vs POA (W/m²)
              </p>
              <p className="text-xs text-subtle mb-4">
                POA is the irradiance hitting your tilted panels  
                higher than GHI when panels face the sun optimally
              </p>

              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={chartData}>
                  <XAxis
                    dataKey="time"
                    tickFormatter={value => formatHourFr(value)}
                    tick={{ fontSize: 10, fill: '#8fb3c4' }}
                    tickLine={false}
                    axisLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: '#8fb3c4' }}
                    tickLine={false}
                    axisLine={false}
                    unit=" W/m²"
                    width={52}
                  />
                  <Tooltip
                    labelFormatter={value =>
                        new Date(value).toLocaleString('fr-FR', {
                          weekday: 'short',
                          day: '2-digit',
                          month: 'short',
                          hour: '2-digit',
                          minute: '2-digit',
                          timeZone: 'Europe/Paris',
                        })
                      }                  
                    formatter={(v, name) => [
                      `${v} W/m²`,
                      name === 'ghi_wm2' ? 'GHI (horizontal)' : 'POA (panel surface)'
                    ]}
                    contentStyle={{
                      border: '0.5px solid #24456a',
                      borderRadius: '8px',
                      fontSize: 12,
                    }}
                  />
                  <Legend
                    iconType="line"
                    iconSize={16}
                    formatter={v => v === 'ghi_wm2' ? 'GHI' : 'POA'}
                    wrapperStyle={{ fontSize: 11, color: '#8fb3c4' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="ghi_wm2"
                    stroke="#5cbdb9"
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