import Navbar from '../components/common/Navbar'
import { Link } from 'react-router-dom'

function HomePage() {

    return (
        <div className="min-h-screen bg-white">
            <Navbar />

            <div className="max-w-3xl mx-auto px-8 pt-20 pb-12">

                {/* Hero */}
                <div className="text-center mb-14">
                    <h1 className="text-3xl font-medium text-gray-900 mb-3">
                        French weather, from the source
                    </h1>
                    <p className="text-base text-gray-500">
                        Real observations and AROME model forecasts - updated continuously.
                    </p>
                </div>

                {/* Cards: each card is a link that allows to navigate to another page */}
                <div className="grid grid-cols-2 gap-4">

                    {/* Weather viewer link: pressing it sends you to weather viewer page */}
                    <Link to="/viewer" className="bg-white border border-gray-100 rounded-xl p-7 cursor-pointer hover:border-gray-300 transition-colors block">
                        <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-xl mb-4">
                            🌤
                        </div>
                        <h2 className="text-base font-medium text-gray-900 mb-2">Weather viewer</h2>
                        <p className="text-sm text-gray-400 mb-5 leading-relaxed">
                            See the forecast for the next days at a glance — temperature, rain, wind.
                        </p>
                        <span className="text-sm font-medium text-blue-800">Go to viewer →</span>
                    </Link>

                    {/* Weather analysis link: pressing it sends you to weather analysis page */}
                    <Link to="analysis" className="bg-white border border-gray-100 rounded-xl p-7 cursor-pointer hover:border-gray-300 transition-colors block">
                        <div className="w-10 h-10 bg-teal-50 rounded-lg flex items-center justify-center text-xl mb-4">
                            📊
                        </div>
                        <h2 className="text-base font-medium text-gray-900 mb-2">Analysis tool</h2>
                        <p className="text-sm text-gray-400 mb-5 leading-relaxed">
                            Compare stations, explore historical data and export CSV files.
                        </p>
                        <span className="text-sm font-medium text-blue-800">Go to analyser →</span>
                    </Link>

                </div>

                {/* Footer note */}
                <p className="text-center text-xs text-gray-300 mt-16">
                    Data source: Météo-France · Updated every 6 minutes
                </p>

            </div>
        </div>
    )
}

export default HomePage