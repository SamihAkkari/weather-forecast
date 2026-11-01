const METEOCONS_BASE_URL = "https://cdn.meteocons.com/3.0.0-next.10/svg/fill";

const WEATHER_ICONS = {
  0: ["clear-day", "clear-night"],
  1: ["mostly-clear-day", "mostly-clear-night"],
  2: ["partly-cloudy-day", "partly-cloudy-night"],
  3: "overcast",
  45: ["fog-day", "fog-night"],
  48: ["fog-day", "fog-night"],
  51: "drizzle",
  53: "drizzle",
  55: "drizzle",
  56: "sleet",
  57: "sleet",
  61: "rain",
  63: "rain",
  65: "extreme-rain",
  66: "sleet",
  67: "sleet",
  71: "snow",
  73: "snow",
  75: "extreme-snow",
  77: "snow",
  80: "rain",
  81: "rain",
  82: "extreme-rain",
  85: "snow",
  86: "extreme-snow",
  95: ["thunderstorms-day", "thunderstorms-night"],
  96: "thunderstorms-snow",
  97: ["thunderstorms-day", "thunderstorms-night"],
  99: "thunderstorms-snow",
};

export function getHourlyWeatherIconName(weatherCode, isDay = true) {
  const icon = WEATHER_ICONS[Number(weatherCode)];
  if (Array.isArray(icon)) {
    return icon[isDay ? 0 : 1];
  }
  return icon ?? "not-available";
}

export function getDailyWeatherIconName(weatherCode) {
  const code = Number(weatherCode);
  if (code === 96 || code === 99) {
    return "hail";
  }
  const icon = WEATHER_ICONS[code];
  if (Array.isArray(icon)) {
    return icon[0];
  }
  return icon ?? "clear-day";
}

export function getWeatherIconUrl(iconName) {
  return `${METEOCONS_BASE_URL}/${iconName}.svg`;
}
