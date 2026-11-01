import ValueWithUnit from "../common/ValueWithUnit";
import { formatHourFr } from "../../utils/time";
import { getHourlyWeatherIconName, getWeatherIconUrl } from "../../utils/weatherIcons";
import * as SunCalcNs from "suncalc";
const SunCalc = SunCalcNs.default ?? SunCalcNs;

function getWeatherIcon(entry, location) {
  const isDay = !isNight(entry.time_step_fr, location.lat, location.lng);
  const iconName = getHourlyWeatherIconName(entry.weather_code, isDay);

  return (
    <img
      src={getWeatherIconUrl(iconName)}
      alt={`Weather code ${entry.weather_code}`}
      className="w-10 h-10 mx-auto"
    />
  );
}

function isNight(timeString, lat, lng) {
  const date = new Date(timeString);

  const sunTimes = SunCalc.getTimes(date, lat, lng);

  const sunrise = sunTimes.sunrise;
  const sunset = sunTimes.sunset;

  return date < sunrise || date > sunset;
}

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
