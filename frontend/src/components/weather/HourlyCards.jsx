import ValueWithUnit from "../common/ValueWithUnit";
import SunCalc from "suncalc";

function getWeatherIcon(entry, location) {
    // console.log(location)
    const isDay = !isNight(entry.time_step_fr, location.lat, location.lng)

    const {
        cape = 0,
        precipitation_mm: precip = 0,
        snow_mm: snow = 0,
        total_cloud_cover: tcc = 0
    } = entry

    // --- 1. Precipitation first (highest priority)
    if (cape > 500 && precip > 0.5) {
        return "⛈️"
    }

    if (snow > 0.1) {
        return "🌨️"
    }

    if (precip > 2.0) {
        return "🌧️"
    }

    if (precip > 0.1) {
        if (tcc < 70) {
            return isDay ? "🌦️" : "🌧️🌙"
            }
        return  "🌧️"
    }

    // --- 2. Sky conditions (no precipitation)
    if (tcc < 12) {
        return isDay
            ? "☀️" 
            : "🌙" 
    }

    if (tcc < 37) {
        return isDay
            ? "🌤️" 
            : "🌙✨" 
    }

    if (tcc < 62) {
        return isDay ? "⛅" : "☁️🌙"
    }

    return "☁️"
}

function isNight(timeString, lat, lng) {
    console.log("RAW STRING:", timeString)
    const date = new Date(timeString)

    date.setHours(date.getHours() - 2) // Quick fix to handle the +00:00 timezone issue, need to fix it in the backend

    const sunTimes = SunCalc.getTimes(date, lat, lng)

    const sunrise = sunTimes.sunrise
    const sunset = sunTimes.sunset

    return date < sunrise || date > sunset
}

// function formatHour(timeString) {
//     const date = new Date(timeString)
//     return `${date.getHours()}:00`
// }

// The API returns the values in France time but with +00:00 timezone which makes the js think it is UTC, now this is a quick fix here but need to fix it in the backend
function formatHour(timeString) {
    const date = new Date(timeString)
    return `${date.getUTCHours()}:00`
}

function HourlyCards({ forecast, location }) {
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
                        {/* <p className="text-base mb-2">{getWeatherIcon(entry.precipitation_mm)}</p> */}
                        <p className="text-base mb-2">{getWeatherIcon(entry, location)}</p>
                        <p className="text-sm font-medium text-gray-900 mb-1">
                            <ValueWithUnit
                                value={entry.temperature_celsius}
                                unit="°C"
                                format={(v) => Math.round(v)}
                            />
                        </p>
                        <p className="text-xs text-gray-400">
                            <ValueWithUnit
                                value={entry.precipitation_mm}
                                unit=" mm"
                                format={(v) => v.toFixed(2)}
                            />
                        </p>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default HourlyCards