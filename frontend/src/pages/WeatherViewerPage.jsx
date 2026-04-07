import Navbar from '../components/common/Navbar'
import StationSummary from '../components/weather/StationSummary'
import TemperatureChart from '../components/weather/TemperatureChart'
import { mockStation, mockCurrentConditions, mockForecast } from '../data/mockData'
import HourlyCards from '../components/weather/HourlyCards'

function WeatherViewerPage() {
    return (
        <div className="min-h-screen bg-white">
            <title> Weather viewer </title>
            <Navbar />

            <div className="max-w-4xl mx-auto px-8 py-8">

                <div className="grid grid-cols-2 gap-4 mb-6">
                    {/* Map placeholder for now */}
                    <div className="border border-gray-100 rounded-xl h-64 bg-gray-50 flex items-center justify-center">
                        <p className="text-sm text-gray-400">Map coming soon</p>
                    </div>

                    {/* Station current conditions summary */}
                    <StationSummary
                        station={mockStation}
                        conditions={mockCurrentConditions}
                    />
                </div>

                {/* Chart and hourly cards coming next */}
                <TemperatureChart forecast={mockForecast} />

                {/* Hourly forecast cards */}
                <HourlyCards forecast={mockForecast} />

            </div>

        </div>

    );
}

export default WeatherViewerPage