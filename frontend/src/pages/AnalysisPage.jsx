import { useState } from 'react'
import Navbar from '../components/common/Navbar'
import StationMap from '../components/weather/StationMap'
import TemperatureAnalysis from '../components/analysis/TemperatureAnalysis'
import WindAnalysis from '../components/analysis/WindAnalysis'
import DetectionAnalysis from '../components/analysis/DetectionAnalysis'
import { exportAnalysisCsv } from '../utils/exportCsv'
import { useAnalysis } from '../hooks/useAnalysis'

/*
  VariableWidget is the expandable card pattern.
  It shows a header row with label, headline metric and a toggle arrow.
  Clicking it expands to show the full detail component below.
*/
function VariableWidget({ label, icon, headline, children, accentColor }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-gray-100 rounded-xl overflow-hidden">

      {/* Header — always visible, clickable to toggle */}
      <div
        onClick={() => setExpanded(prev => !prev)}
        className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-base">{icon}</span>
          <div>
            <p className="text-sm font-medium text-gray-900">{label}</p>
            {headline && (
              <p className="text-xs text-gray-400 mt-0.5">{headline}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/*
            Small colored pill showing the headline metric.
            Color is passed as a Tailwind class string from the parent.
          */}
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{
              background: `${accentColor}18`,
              color: accentColor,
            }}
          >
            {headline}
          </span>
          <span
            className="text-gray-400 text-xs transition-transform"
            style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)' }}
          >
            ▼
          </span>
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-gray-50 px-5 py-5">
          {children}
        </div>
      )}

    </div>
  )
}

function AnalysisPage() {
  const [location, setLocation]   = useState(null)
  const [useAllStations, setUseAllStations] = useState(true)
  const [days, setDays]           = useState(7)
  const { analysisData, loading, error, runAnalysis } = useAnalysis()

  function handleAnalyse() {
    if (useAllStations) {
      runAnalysis(null, null, days)
    } else {
      if (!location) return
      runAnalysis(location.lat, location.lng, days)
    }
  }

  /*
    Headline metrics shown in each widget header
    before the user expands — gives instant value.
  */
  const tempHeadline = analysisData
    ? `MAE ${analysisData.temperature.mae}°C`
    : null
  const windHeadline = analysisData
    ? `MAE ${analysisData.wind.mae} m/s`
    : null
  const rainHeadline = analysisData
    ? `F1 ${Math.round(analysisData.rain.f1 * 100)}%`
    : null

  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      <div className="max-w-4xl mx-auto px-8 py-8">

        <div className="mb-8">
          <h1 className="text-xl font-medium text-gray-900 mb-1">
            Forecast model analysis
          </h1>
          <p className="text-sm text-gray-400">
            Evaluate AROME model accuracy against real observations
          </p>
        </div>

        {/* Selector bar */}
        <div className="border border-gray-100 rounded-xl p-5 mb-6">

          {/* All stations vs specific location toggle */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setUseAllStations(true)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                useAllStations
                  ? 'border-gray-900 bg-gray-900 text-white'
                  : 'border-gray-100 text-gray-500 hover:border-gray-300'
              }`}
            >
              All stations
            </button>
            <button
              onClick={() => setUseAllStations(false)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                !useAllStations
                  ? 'border-gray-900 bg-gray-900 text-white'
                  : 'border-gray-100 text-gray-500 hover:border-gray-300'
              }`}
            >
              Specific location
            </button>
          </div>

          {/*
            Map only shown when user selects specific location.
            Same StationMap component reused from viewer page.
          */}
          {!useAllStations && (
            <div className="mb-4">
              <p className="text-xs text-gray-400 mb-1.5">Select a location</p>
              <StationMap
                selectedLocation={location}
                onLocationClick={setLocation}
              />
              {location && (
                <p className="text-xs text-gray-400 mt-1.5">
                  📍 {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
                </p>
              )}
            </div>
          )}

          {/* Days input + buttons */}
          <div className="flex gap-3 items-end">
            <div className="w-36">
              <p className="text-xs text-gray-400 mb-1.5">History (days)</p>
              <input
                type="number"
                min={1} max={90}
                value={days}
                onChange={e => setDays(parseInt(e.target.value))}
                className="w-full border border-gray-100 rounded-lg px-3 py-2 text-sm text-gray-600 focus:outline-none focus:border-gray-300"
              />
            </div>

            <button
              onClick={handleAnalyse}
              disabled={(!useAllStations && !location) || loading}
              className="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? 'Analysing...' : 'Analyse'}
            </button>

            <button
              onClick={() => exportAnalysisCsv(analysisData, `${days}days`)}
              disabled={!analysisData}
              className="px-4 py-2 border border-gray-100 rounded-lg text-sm text-gray-500 hover:border-gray-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Export CSV
            </button>
          </div>

        </div>

        {/* Meta info shown after analysis */}
        {analysisData && !loading && (
          <div className="text-xs text-gray-400 mb-4">
            {analysisData.meta.station_id
              ? `Nearest station to selected location`
              : 'Aggregated over all stations'
            }
            {' · '}
            {new Date(analysisData.meta.date_from).toLocaleDateString('fr-FR')}
            {' → '}
            {new Date(analysisData.meta.date_to).toLocaleDateString('fr-FR')}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center py-16 text-gray-400 text-sm">
            Computing analysis...
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="text-center py-16 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Expandable variable widgets */}
        {analysisData && !loading && (
          <div className="space-y-3">

            <VariableWidget
              label="Temperature"
              icon="🌡"
              headline={tempHeadline}
              accentColor="#378ADD"
            >
              <TemperatureAnalysis data={analysisData.temperature} />
            </VariableWidget>

            <VariableWidget
              label="Wind speed"
              icon="💨"
              headline={windHeadline}
              accentColor="#a78bfa"
            >
              <WindAnalysis data={analysisData.wind} />
            </VariableWidget>

            <VariableWidget
              label="Rain detection"
              icon="🌧"
              headline={rainHeadline}
              accentColor="#60a5fa"
            >
              <DetectionAnalysis data={analysisData.rain} />
            </VariableWidget>

          </div>
        )}

      </div>
    </div>
  )
}

export default AnalysisPage