import { useState } from 'react'
import Navbar from '../components/common/Navbar'
import StationMap from '../components/weather/StationMap'
import { mockAnalysis } from '../data/mockData'
import TemperatureAnalysis from '../components/analysis/TemperatureAnalysis'
import DetectionAnalysis from '../components/analysis/DetectionAnalysis'
import { exportAnalysisCsv } from '../utils/exportCsv'

function AnalysisPage() {
    const [location, setLocation] = useState(null)
    const [runTime, setRunTime] = useState('')
    const [analysisData, setAnalysisData] = useState(null)

    function handleAnalyse() {
        if (!location || !runTime) return
        setAnalysisData(mockAnalysis)
    }

    return (
        <div className="min-h-screen bg-white">
            <Navbar />

            <div className="max-w-4xl mx-auto px-8 py-8">

                <div className="mb-8">
                    <h1 className="text-xl font-medium text-gray-900 mb-1">Forecast model analysis</h1>
                    <p className="text-sm text-gray-400">Compare AROME predictions against real observations</p>
                </div>

                {/* Selector bar */}
                <div className="flex gap-3 items-end mb-8">

                    <div className="flex-1">
                        <p className="text-xs text-gray-400 mb-1.5">Location</p>
                        {/*
              This div just displays the selected coordinates as text.
              It is not an input — the user selects the location via the map below.
              location?.lat uses optional chaining so it doesn't crash if location is null.
              toFixed(4) rounds the coordinate to 4 decimal places for readability.
            */}
                        <div className="border border-gray-100 rounded-lg px-3 py-2 text-sm text-gray-400">
                            {location
                                ? `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}`
                                : 'Click on the map below to select'}
                        </div>
                    </div>

                    <div className="flex-1">
                        <p className="text-xs text-gray-400 mb-1.5">Forecast run</p>
                        {/*
              datetime-local is a native HTML input that shows a date + time picker.
              The value is a string in the format "2026-04-21T00:00".
              We store it in runTime state and will send it to the backend later.
            */}
                        <input
                            type="datetime-local"
                            value={runTime}
                            onChange={e => setRunTime(e.target.value)}
                            className="w-full border border-gray-100 rounded-lg px-3 py-2 text-sm text-gray-600 focus:outline-none focus:border-gray-300"
                        />
                    </div>

                    <button
                        onClick={handleAnalyse}
                        disabled={!location || !runTime}
                        className="px-4 py-2 border border-gray-100 rounded-lg text-sm text-gray-700 hover:border-gray-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        Analyse
                    </button>

                    <button
                        onClick={() => exportAnalysisCsv(analysisData, runTime)}
                        disabled={!analysisData}
                        className="px-4 py-2 border border-gray-100 rounded-lg text-sm text-gray-500 hover:border-gray-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        Export CSV
                    </button>

                </div>

                {/* 
          Map section.
          We reuse StationMap exactly as we built it for the viewer page.
          - selectedLocation: the current marker position on the map
          - onLocationClick: called whenever the user clicks the map or submits an address search.
            We pass setLocation directly — when the user clicks, setLocation receives
            {lat, lng} and React re-renders, which updates the coordinates display above.
        */}
                <div className="mb-8">
                    <p className="text-xs text-gray-400 mb-1.5">Select a location</p>
                    <StationMap
                        selectedLocation={location}
                        onLocationClick={setLocation}
                    />
                </div>

                {/*
          Results section.
          The && operator means: only render what comes after if analysisData is not null.
          So nothing appears here until the user clicks Analyse.
          We wrap everything in a div with space-y-4 which adds vertical gap between child elements.
        */}
                {analysisData && (
                    <div className="space-y-4">
                        <p className="text-sm text-gray-500">
                            Nearest station: <span className="font-medium text-gray-900">{analysisData.station_name}</span>
                        </p>
                        <TemperatureAnalysis data={analysisData.temperature} />

                        {/*
                        Both use the same DetectionAnalysis component.
                        The only difference is the title prop and which data object we pass.
                        rain and sunshine have identical shapes so the component handles both perfectly.
                        */}
                        <div className="grid grid-cols-2 gap-4">
                            <DetectionAnalysis
                                title="Rain detection"
                                data={analysisData.rain}
                            />
                            <DetectionAnalysis
                                title="Sunshine detection"
                                data={analysisData.sunshine}
                            />
                        </div>
                    </div>
                )}

            </div>
        </div>
    )
}

export default AnalysisPage