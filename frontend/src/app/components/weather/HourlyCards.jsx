import ValueWithUnit from "../common/ValueWithUnit";
import { formatHourFr } from "../../utils/time";
import * as SunCalcNs from "suncalc";
const SunCalc = SunCalcNs.default ?? SunCalcNs;

function getWeatherIcon(entry, location) {
  // console.log(location)
  const isDay = !isNight(entry.time_step_fr, location.lat, location.lng);

  const icons = {
    0: isDay ? "☀️" : "🌙",
    1: isDay ? "🌤️" : "🌙",
    2: isDay ? "⛅" : "☁️",
    3: "☁️",
    45: "🌫️",
    48: "🌫️",
    51: "🌦️",
    53: "🌦️",
    55: "🌧️",
    56: "🌧️",
    57: "🌧️",
    61: "🌧️",
    63: "🌧️",
    65: "🌧️",
    66: "🌧️",
    67: "🌧️",
    71: "🌨️",
    73: "🌨️",
    75: "❄️",
    77: "🌨️",
    80: "🌧️",
    81: "🌧️",
    82: "🌧️",
    85: "🌨️",
    86: "❄️",
    95: isDay ? "⛈️" : "🌩️",
    96: "⛈️",
    97: isDay ? "⛈️" : "🌩️",
    99: "⛈️",
  };

  const icon = icons[Number(entry.weather_code)] ?? "🌤️";

  return (
    <span role="img" aria-label={`Weather code ${entry.weather_code}`} className="text-3xl">
      {icon}
    </span>
  );
}

function isNight(timeString, lat, lng) {
  // console.log("RAW STRING:", timeString)
  const date = new Date(timeString);

  // date.setHours(date.getHours() - 2) // Quick fix to handle the +00:00 timezone issue, need to fix it in the backend

  const sunTimes = SunCalc.getTimes(date, lat, lng);

  const sunrise = sunTimes.sunrise;
  const sunset = sunTimes.sunset;

  return date < sunrise || date > sunset;
}

// function formatHour(timeString) {
//     const date = new Date(timeString)
//     return `${date.getHours()}:00`
// }

// The API returns the values in France time but with +00:00 timezone which makes the js think it is UTC, now this is a quick fix here but need to fix it in the backend
// function formatHour(timeString) {
//     const date = new Date(timeString)
//     return `${date.getUTCHours()}:00`
// }

function HourlyCards({ forecast, location }) {
  return (
    <div>
      <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-primary mb-4">
        Hourly forecast
      </p>
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
            className="min-w-20 glass lift border border-border rounded-2xl p-3 text-center flex-shrink-0"
          >
            <p className="text-xs text-muted-foreground mb-2">{formatHourFr(entry.time_step_fr)}</p>
            {/* <p className="text-base mb-2">{getWeatherIcon(entry.precipitation_mm)}</p> */}
            <p className="mb-2">{getWeatherIcon(entry, location)}</p>
            <p className="text-sm font-medium text-foreground mb-1">
              <ValueWithUnit
                value={entry.temperature_celsius}
                unit="°C"
                format={(v) => Math.round(v)}
              />
            </p>
            <p className="text-xs text-muted-foreground">
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
  );
}

export default HourlyCards;
