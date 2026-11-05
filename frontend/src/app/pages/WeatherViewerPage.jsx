import Navbar from '../components/common/Navbar'
import StationMap from '../components/weather/StationMap'
import HourlyCards from '../components/weather/HourlyCards'
import DailyForecast from '../components/weather/DailyForecast'
import WeatherWidgets from '../components/weather/WeatherWidgets'
import useStationData from '../hooks/useStationData'
import LifestyleWidget from '../components/weather/LifestyleWidget'
import { useNavigate } from '../router-compat'

// import { mockCurrentConditions, mockStation, mockForecast, mockWeatherDetails } from '../data/mockData'
// import { mockLifestyle } from '../data/mockData'

function PvEntryCard({ location }) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate('/pv', { state: { location } })}
      className="relative overflow-hidden glass border border-border rounded-3xl p-6 cursor-pointer lift group"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-muted-foreground mb-1">Energy</p>
          <p className="text-sm font-medium text-foreground mb-1">
            ☀️ Evaluate your potential PV production
          </p>
          <p className="text-xs text-muted-foreground">
            Estimate hourly solar output for your installation over the forecast period
          </p>
        </div>
        <span className="text-subtle group-hover:text-muted-foreground transition-colors text-lg ml-4">
          →
        </span>
      </div>
    </div>
  )
}

function WeatherViewerPage({ selectedLocation, onLocationChange }) {
  const { stationData, loading, error } = useStationData(selectedLocation)

  return (
    <div className="min-h-screen">
      <Navbar />

      <div className="max-w-6xl mx-auto px-6 py-10">

        <div className="mb-8 animate-rise">
          <p className="text-xs uppercase tracking-[0.2em] text-primary mb-2">Forecast explorer</p>
          <h1 className="text-3xl sm:text-4xl font-semibold text-foreground">Where's the weather taking you?</h1>
          <p className="mt-2 text-muted-foreground">Click anywhere on the map or search an address.</p>
        </div>

        <div className="mb-8 animate-rise">
          <StationMap
            selectedLocation={selectedLocation}
            onLocationClick={onLocationChange}
          />
        </div>


        {/* Empty state   before any location is selected */}
        {!selectedLocation && !stationData && (
          <div className="glass border border-dashed border-border rounded-3xl text-center py-16 text-muted-foreground text-sm">
            <div className="text-4xl mb-3 animate-float">📍</div>
            Drop a pin to reveal the forecast
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="space-y-4">
            {[0,1,2].map(i => <div key={i} className="h-28 rounded-3xl bg-muted animate-pulse" />)}
          </div>
        )}

        {/* Error state */}
        {error && !loading && (
          <div className="text-center py-20 text-destructive text-sm">
            {error}
          </div>
        )}

        {/* Data   only shown when stationData is available */}
        {stationData && !loading && (
          <div className="space-y-8 animate-rise">

            {/* Station name */}
            <div className="flex items-center gap-3">
              <span className="h-2.5 w-2.5 rounded-full bg-primary shadow-[var(--shadow-glow)]" />
              <p className="text-sm text-muted-foreground">Nearest station</p>
              <h2 className="text-2xl font-semibold text-foreground">{stationData.station?.location_name}</h2>
            </div>

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