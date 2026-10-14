// import { useState } from 'react'
// import Navbar from '../components/common/Navbar'
// import StationSummary from '../components/weather/StationSummary'
// import TemperatureChart from '../components/weather/TemperatureChart'
// // import { mockStation, mockCurrentConditions, mockForecast, mockStations } from '../data/mockData'
// // import { mockStations, mockWeatherByStation } from '../data/mockData'
// import HourlyCards from '../components/weather/HourlyCards'

// import StationMap from '../components/weather/StationMap'

// // import useStations from '../hooks/useStations'
// import useStationData from '../hooks/useStationData'

// import DailyForecast from '../components/weather/DailyForecast'

// import { mockWeatherDetails } from '../data/mockData'

// function WeatherViewerPage() {
//     // const [selectedStation, setSelectedStation] = useState(null)
//     // const { stations, loading: loadingStations } = useStations()
//     // const { stationData, loading: loadingData } = useStationData(selectedStation?.id)

//     const [selectedLocation, setSelectedLocation] = useState(null)
//     const { stationData, loading: loadingData } = useStationData(selectedLocation)

//     // const [selectedStation, setSelectedStation] = useState(mockStations[0])
//     // const stationData = mockWeatherByStation[selectedStation?.id]

//     return (
//         <div className="min-h-screen bg-white">
//             <title> Weather viewer </title>
//             <Navbar />

//             <div className="max-w-4xl mx-auto px-8 py-8">

//                 <div className="grid grid-cols-2 gap-4 mb-6">
//                     {/* Map card */}
//                     <StationMap
//                         selectedLocation={selectedLocation}
//                         onLocationClick={setSelectedLocation}
//                     />

//                     {/* Station current conditions summary */}
//                     {stationData ? (
//                         <StationSummary
//                             station_info={stationData.station_info}
//                             conditions={stationData.conditions}
//                         />
//                     ) : (
//                         <div className="border border-gray-100 rounded-xl h-64 flex items-center justify-center">
//                             <p className="text-sm text-gray-400">
//                                 {loadingData ? 'Loading...' : 'Click anywhere on the map'}
//                             </p>
//                         </div>
//                     )}
//                 </div>
//                 {stationData && (
//                     <>
//                         <TemperatureChart forecast={stationData.forecast} />
//                         <HourlyCards forecast={stationData.forecast} location={selectedLocation} />
//                         <div className="mt-6">
//                             <DailyForecast daily={mockWeatherDetails.daily} />
//                         </div>
//                     </>
//                 )}

//                 {loadingData && (
//                     <div className="text-center py-16 text-gray-400 text-sm">
//                         Loading station data...
//                     </div>
//                 )}

//             </div>

//         </div >

//     );
// }

// export default WeatherViewerPage

import { useState } from 'react'
import Navbar from '../components/common/Navbar'
import StationMap from '../components/weather/StationMap'
import StationSummary from '../components/weather/StationSummary'
import TemperatureChart from '../components/weather/TemperatureChart'
import HourlyCards from '../components/weather/HourlyCards'
import DailyForecast from '../components/weather/DailyForecast'
// import { useStationData } from '../hooks/useStationData'
import { mockCurrentConditions, mockStation, mockForecast, mockWeatherDetails } from '../data/mockData'

import WeatherWidgets from '../components/weather/WeatherWidgets'
import useStationData from '../hooks/useStationData'

import LifestyleWidget from '../components/weather/LifestyleWidget'
import { mockLifestyle } from '../data/mockData'

function WeatherViewerPage() {
  const [selectedLocation, setSelectedLocation] = useState(null)
  const { stationData, loading: loadingData } = useStationData(selectedLocation)

  /*
    If stationData exists use it, otherwise fall back to mock data.
    This way the page always shows something useful even before
    the user selects a location or before the backend is connected.
  */
  const displayData = stationData ?? {
    station: mockStation,
    conditions: mockCurrentConditions,
    forecast: mockForecast,
    details: mockWeatherDetails,
  }

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

        <div className="space-y-6">
          <HourlyCards 
            forecast={displayData.forecast} 
            location={displayData.station}
          />
          <DailyForecast daily={mockWeatherDetails.daily} />
          <WeatherWidgets widgets={mockWeatherDetails.widgets} />
          <LifestyleWidget activities={mockLifestyle.activities} />
        </div>

      </div>
    </div>
  )
}

export default WeatherViewerPage