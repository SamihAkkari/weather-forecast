import { useState } from 'react'
import Navbar from '../components/common/Navbar'
import StationMap from '../components/weather/StationMap'
import HourlyCards from '../components/weather/HourlyCards'
import DailyForecast from '../components/weather/DailyForecast'
import WeatherWidgets from '../components/weather/WeatherWidgets'
import useStationData from '../hooks/useStationData'
import LifestyleWidget from '../components/weather/LifestyleWidget'

// import { mockCurrentConditions, mockStation, mockForecast, mockWeatherDetails } from '../data/mockData'
// import { mockLifestyle } from '../data/mockData'

function WeatherViewerPage() {
  const [selectedLocation, setSelectedLocation] = useState(null)
  const { stationData, loading, error } = useStationData(selectedLocation)

  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      <div className="max-w-4xl mx-auto px-8 py-8">

        <div className="mb-6">
          <StationMap
            selectedLocation={selectedLocation}
            onLocationClick={setSelectedLocation}
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
            <LifestyleWidget activities={stationData.lifestyle.activities} />

          </div>
        )}

      </div>
    </div>
  )
}

export default WeatherViewerPage