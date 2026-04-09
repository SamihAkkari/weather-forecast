import { useState } from 'react'
import Navbar from '../components/common/Navbar'
import StationSummary from '../components/weather/StationSummary'
import TemperatureChart from '../components/weather/TemperatureChart'
// import { mockStation, mockCurrentConditions, mockForecast, mockStations } from '../data/mockData'
// import { mockStations, mockWeatherByStation } from '../data/mockData'
import HourlyCards from '../components/weather/HourlyCards'

import StationMap from '../components/weather/StationMap'

import useStations from '../hooks/useStations'
import useStationData from '../hooks/useStationData'

function WeatherViewerPage() {
    const [selectedStation, setSelectedStation] = useState(null)
    const { stations, loading: loadingStations } = useStations()
    const { stationData, loading: loadingData } = useStationData(selectedStation?.id)
    
    // const [selectedStation, setSelectedStation] = useState(mockStations[0])
    // const stationData = mockWeatherByStation[selectedStation?.id]

    return (
        <div className="min-h-screen bg-white">
            <title> Weather viewer </title>
            <Navbar />

            <div className="max-w-4xl mx-auto px-8 py-8">

                <div className="grid grid-cols-2 gap-4 mb-6">
                    {/* Map card */}
                    <StationMap
                        stations={stations}
                        selectedStation={selectedStation}
                        onStationClick={setSelectedStation}
                    />

                    {/* Station current conditions summary */}
                    {stationData ? (
                        <StationSummary
                            station={selectedStation}
                            conditions={stationData.conditions}
                        />
                    ) : (
                        <div className="border border-gray-100 rounded-xl h-64 flex items-center justify-center">
                            <p className="text-sm text-gray-400">No data available for this station yet</p>
                        </div>
                    )}
                </div>

                {stationData ? (
                    <>
                        {/* Chart and hourly cards coming next */}
                        <TemperatureChart forecast={stationData.forecast} />

                        {/* Hourly forecast cards */}
                        <HourlyCards forecast={stationData.forecast} />
                    </>
                ) : (
                    <div className="text-center py-16 text-gray-400 text-sm">
                        No data available for this station yet.
                    </div>
                )}

            </div>

        </div >

    );
}

export default WeatherViewerPage