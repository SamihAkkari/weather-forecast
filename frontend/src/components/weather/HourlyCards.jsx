function getWeatherIcon(precipitation) {
    if (precipitation > 0.5) return '🌧'
    if (precipitation > 0.1) return '🌦'
    return '🌤'
}

function formatHour(timeString) {
    const date = new Date(timeString)
    return `${date.getHours()}:00`
}

function HourlyCards({ forecast }) {
    return (
        <div>
            <p className="text-xs text-gray-400 mb-3">Hourly forecast</p>
            {/* 
            flex: to show the cards horizontally
            gap-2: show add a gap between the cards
            overflow-x-auto: to put them on the full page with a sub scrolling
            pb-3: to position the scroller
            */}
            <div className="flex gap-2 overflow-x-auto pb-3">
                {forecast.map((entry, index) => (
                    <div
                        key={index}
                        className="min-w-20 border border-gray-100 rounded-xl p-3 text-center flex-shrink-0">
                        <p className="text-xs text-gray-400 mb-2">{formatHour(entry.time_step_fr)}</p>
                        <p className="text-base mb-2">{getWeatherIcon(entry.precipitation_mm)}</p>
                        <p className="text-sm font-medium text-gray-900 mb-1">{entry.temperature_celsius}°</p>
                        <p className="text-xs text-gray-400">{entry.precipitation_mm}mm</p>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default HourlyCards