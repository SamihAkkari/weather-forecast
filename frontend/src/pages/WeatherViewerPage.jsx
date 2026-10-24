import Navbar from '../components/common/Navbar'
import StationMap from '../components/weather/StationMap'
import HourlyCards from '../components/weather/HourlyCards'
import DailyForecast from '../components/weather/DailyForecast'
import WeatherWidgets from '../components/weather/WeatherWidgets'
import useStationData from '../hooks/useStationData'
import LifestyleWidget from '../components/weather/LifestyleWidget'
import { useNavigate } from 'react-router-dom'

// import { mockCurrentConditions, mockStation, mockForecast, mockWeatherDetails } from '../data/mockData'
// import { mockLifestyle } from '../data/mockData'

function PvEntryCard({ location }) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate('/pv', { state: { location } })}
      className="border border-gray-100 rounded-xl p-5 cursor-pointer hover:border-gray-300 transition-colors group"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-400 mb-1">Energy</p>
          <p className="text-sm font-medium text-gray-900 mb-1">
            ☀️ Evaluate your potential PV production
          </p>
          <p className="text-xs text-gray-400">
            Estimate hourly solar output for your installation over the forecast period
          </p>
        </div>
        <span className="text-gray-300 group-hover:text-gray-400 transition-colors text-lg ml-4">
          →
        </span>
      </div>
    </div>
  )
}

function WeatherViewerPage({ selectedLocation, onLocationChange }) {
  const { stationData, loading, error } = useStationData(selectedLocation)

  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      <div className="max-w-4xl mx-auto px-8 py-8">

        <div className="mb-6">
          <StationMap
            selectedLocation={selectedLocation}
            onLocationClick={onLocationChange}
          />
        </div>


        {/* Empty state — before any location is selected */}
        {!selectedLocation && !stationData && (
          <div className="text-center py-20 text-gray-400 text-sm">
            Click anywhere on the map or search an address to see the forecast
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="text-center py-20 text-gray-400 text-sm">
            Loading forecast...
          </div>
        )}

        {/* Error state */}
        {error && !loading && (
          <div className="text-center py-20 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Data — only shown when stationData is available */}
        {stationData && !loading && (
          <div className="space-y-6">

            {/* Station name */}
            <p className="text-sm text-gray-500">
              Nearest station:{' '}
              <span className="font-medium text-gray-900">
                {stationData.station?.location_name}
              </span>
            </p>

            {/* Hourly cards */}
            <HourlyCards forecast={stationData.forecast} location={stationData.station} />

            {/* Daily forecast */}
            <DailyForecast daily={stationData.daily} />

            {/* Weather widgets */}
            <WeatherWidgets widgets={stationData.widgets} />

            {/* Lifestyle widget */}
            <LifestyleWidget activities={stationData.activities} />

            
            {/* Lifestyle widget */}
            <PvEntryCard location={selectedLocation} />

          </div>
        )}

      </div>
    </div>
  )
}

export default WeatherViewerPage