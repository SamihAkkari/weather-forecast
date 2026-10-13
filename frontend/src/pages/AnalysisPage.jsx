import { useState } from 'react'
import Navbar from '../components/common/Navbar'
import StationMap from '../components/weather/StationMap'
import TemperatureAnalysis from '../components/analysis/TemperatureAnalysis'
import DetectionAnalysis from '../components/analysis/DetectionAnalysis'
import { exportAnalysisCsv } from '../utils/exportCsv'
import { useAnalysis } from '../hooks/useAnalysis'

function AnalysisPage() {
  const [location, setLocation] = useState(null)
  const [days, setDays] = useState(7)
  const { analysisData, loading, error, runAnalysis } = useAnalysis()

  function handleAnalyse() {
    if (!location) return
    runAnalysis(location.lat, location.lng, days)
  }

  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      <div className="max-w-4xl mx-auto px-8 py-8">

        <div className="mb-8">
          <h1 className="text-xl font-medium text-gray-900 mb-1">Forecast model analysis</h1>
          <p className="text-sm text-gray-400">
            Aggregate AROME model performance over a selected period
          </p>
        </div>

        <div className="flex gap-3 items-end mb-8">

          <div className="flex-1">
            <p className="text-xs text-gray-400 mb-1.5">Location</p>
            <div className="border border-gray-100 rounded-lg px-3 py-2 text-sm text-gray-400">
              {location
                ? `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}`
                : 'Click on the map below to select'}
            </div>
          </div>

          <div className="w-36">
            <p className="text-xs text-gray-400 mb-1.5">History (days)</p>
            {/*
              A simple number input with a min of 1 and max of 30.
              We default to 7 days which is a reasonable starting point.
              The user can type a number or use the arrow keys to adjust.
            */}
            <input
              type="number"
              min={1}
              max={30}
              value={days}
              onChange={e => setDays(parseInt(e.target.value))}
              className="w-full border border-gray-100 rounded-lg px-3 py-2 text-sm text-gray-600 focus:outline-none focus:border-gray-300"
            />
          </div>

          <button
            onClick={handleAnalyse}
            disabled={!location || loading}
            className="px-4 py-2 border border-gray-100 rounded-lg text-sm text-gray-700 hover:border-gray-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? 'Loading...' : 'Analyse'}
          </button>

          <button
            onClick={() => exportAnalysisCsv(analysisData, `${days}days`)}
            disabled={!analysisData}
            className="px-4 py-2 border border-gray-100 rounded-lg text-sm text-gray-500 hover:border-gray-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Export CSV
          </button>

        </div>

        <div className="mb-8">
          <p className="text-xs text-gray-400 mb-1.5">Select a location</p>
          <StationMap
            selectedLocation={location}
            onLocationClick={setLocation}
          />
        </div>

        {loading && (
          <div className="text-center py-16 text-gray-400 text-sm">
            Computing analysis...
          </div>
        )}

        {error && !loading && (
          <div className="text-center py-16 text-red-400 text-sm">
            {error}
          </div>
        )}

        {analysisData && !loading && (
          <div className="space-y-4">
            <TemperatureAnalysis data={analysisData.temperature} />
            <div className="grid grid-cols-2 gap-4">
              <DetectionAnalysis title="Rain detection" data={analysisData.rain} />
              <DetectionAnalysis title="Sunshine detection" data={analysisData.sunshine} />
            </div>
          </div>
        )}

      </div>
    </div>
  )
}

export default AnalysisPage