export const mockAnalysis = {
  temperature: {
    degradation: {
      1: 0.31, 2: 0.38, 3: 0.45, 4: 0.52, 5: 0.58,
      6: 0.63, 7: 0.69, 8: 0.74, 9: 0.79, 10: 0.83,
      11: 0.87, 12: 0.91, 13: 0.95, 14: 0.99, 15: 1.03,
      16: 1.07, 17: 1.11, 18: 1.15, 19: 1.18, 20: 1.21,
      21: 1.24, 22: 1.27, 23: 1.30, 24: 1.33, 25: 1.36,
      26: 1.38, 27: 1.40, 28: 1.42, 29: 1.44, 30: 1.46,
      31: 1.48, 32: 1.50, 33: 1.52, 34: 1.54, 35: 1.56,
      36: 1.57, 37: 1.58, 38: 1.59, 39: 1.60, 40: 1.61,
      41: 1.62, 42: 1.63, 43: 1.64, 44: 1.65, 45: 1.66,
      46: 1.67, 47: 1.68, 48: 1.69,
    }
  },
  rain: {
    tp: 18, fp: 24, fn: 6, tn: 112,
    precision: 0.43, recall: 0.75, f1: 0.54,
    insight: "The model tends to over-predict rain — 24 false alarms across the period."
  },
  sunshine: {
    tp: 87, fp: 12, fn: 8, tn: 53,
    precision: 0.88, recall: 0.92, f1: 0.90,
    insight: "Sunshine is well captured across the period with strong precision and recall."
  }
}

export const mockWeatherDetails = {
  daily: [
    { day: "Today", icon: "partly_cloudy", min: 8,  max: 17 },
    { day: "Tue",   icon: "sunny",         min: 10, max: 19 },
    { day: "Wed",   icon: "rainy",         min: 6,  max: 16 },
    { day: "Thu",   icon: "sunny",         min: 12, max: 21 },
    { day: "Fri",   icon: "cloudy",        min: 9,  max: 18 },
    { day: "Sat",   icon: "partly_cloudy", min: 7,  max: 17 },
  ],
  widgets: {
    humidity:    { value: 72,   unit: "%",    message: "Quite humid today" },
    feels_like:  { value: 12,   unit: "°C",   message: "Feels colder than actual" },
    wind:        { value: 12,   unit: "m/s",  message: "Northwest, gentle breeze", direction: "NW" },
    sunrise:     { value: "06:42", unit: "",  message: "Sunset at 20:18" },
    uv_index:    { value: 3,    unit: "",     message: "Moderate — no protection needed" },
    visibility:  { value: 10,   unit: "km",   message: "Perfectly clear today" },
    pressure:    { value: 1018, unit: "hPa",  message: "High pressure, stable weather" },
  }
}

export const mockStation = {
  location_name: "Paris-Montsouris",
  latitude: 48.8215,
  longitude: 2.3378,
}

export const mockCurrentConditions = {
  temperature_celsius: 14,
  humidity_percentage: 72,
  wind_speed_m_per_s: 12,
  precipitation_mm: 0.2,
}

export const mockForecast = [
  { time_step_fr_step_fr: "2026-04-21T12:00:00", temperature_celsius: 13, precipitation_mm: 0.0, wind_speed_m_per_s: 10, humidity_percentage: 68 },
  { time_step_fr: "2026-04-21T13:00:00", temperature_celsius: 14, precipitation_mm: 0.0, wind_speed_m_per_s: 11, humidity_percentage: 67 },
  { time_step_fr: "2026-04-21T14:00:00", temperature_celsius: 15, precipitation_mm: 0.0, wind_speed_m_per_s: 12, humidity_percentage: 65 },
  { time_step_fr: "2026-04-21T15:00:00", temperature_celsius: 16, precipitation_mm: 0.1, wind_speed_m_per_s: 13, humidity_percentage: 64 },
  { time_step_fr: "2026-04-21T16:00:00", temperature_celsius: 15, precipitation_mm: 0.2, wind_speed_m_per_s: 14, humidity_percentage: 66 },
  { time_step_fr: "2026-04-21T17:00:00", temperature_celsius: 14, precipitation_mm: 0.5, wind_speed_m_per_s: 13, humidity_percentage: 70 },
  { time_step_fr: "2026-04-21T18:00:00", temperature_celsius: 13, precipitation_mm: 0.3, wind_speed_m_per_s: 11, humidity_percentage: 74 },
  { time_step_fr: "2026-04-21T19:00:00", temperature_celsius: 12, precipitation_mm: 0.0, wind_speed_m_per_s: 10, humidity_percentage: 75 },
  { time_step_fr: "2026-04-21T20:00:00", temperature_celsius: 11, precipitation_mm: 0.0, wind_speed_m_per_s: 9,  humidity_percentage: 76 },
  { time_step_fr: "2026-04-21T21:00:00", temperature_celsius: 10, precipitation_mm: 0.0, wind_speed_m_per_s: 8,  humidity_percentage: 78 },
  { time_step_fr: "2026-04-21T22:00:00", temperature_celsius: 10, precipitation_mm: 0.0, wind_speed_m_per_s: 8,  humidity_percentage: 79 },
  { time_step_fr: "2026-04-21T23:00:00", temperature_celsius: 9,  precipitation_mm: 0.0, wind_speed_m_per_s: 7,  humidity_percentage: 80 },
  { time_step_fr: "2026-04-22T00:00:00", temperature_celsius: 9,  precipitation_mm: 0.0, wind_speed_m_per_s: 7,  humidity_percentage: 81 },
  { time_step_fr: "2026-04-22T01:00:00", temperature_celsius: 8,  precipitation_mm: 0.0, wind_speed_m_per_s: 6,  humidity_percentage: 82 },
  { time_step_fr: "2026-04-22T02:00:00", temperature_celsius: 8,  precipitation_mm: 0.0, wind_speed_m_per_s: 6,  humidity_percentage: 83 },
  { time_step_fr: "2026-04-22T03:00:00", temperature_celsius: 7,  precipitation_mm: 0.1, wind_speed_m_per_s: 6,  humidity_percentage: 84 },
  { time_step_fr: "2026-04-22T04:00:00", temperature_celsius: 7,  precipitation_mm: 0.0, wind_speed_m_per_s: 5,  humidity_percentage: 84 },
  { time_step_fr: "2026-04-22T05:00:00", temperature_celsius: 7,  precipitation_mm: 0.0, wind_speed_m_per_s: 5,  humidity_percentage: 85 },
  { time_step_fr: "2026-04-22T06:00:00", temperature_celsius: 7,  precipitation_mm: 0.0, wind_speed_m_per_s: 5,  humidity_percentage: 85 },
  { time_step_fr: "2026-04-22T07:00:00", temperature_celsius: 8,  precipitation_mm: 0.0, wind_speed_m_per_s: 5,  humidity_percentage: 84 },
  { time_step_fr: "2026-04-22T08:00:00", temperature_celsius: 9,  precipitation_mm: 0.0, wind_speed_m_per_s: 6,  humidity_percentage: 82 },
  { time_step_fr: "2026-04-22T09:00:00", temperature_celsius: 10, precipitation_mm: 0.0, wind_speed_m_per_s: 7,  humidity_percentage: 80 },
]

export const mockLifestyle = {
  activities: [
    { id: "running",      icon: "🏃", label: "Running",      status: "good",   message: "Good conditions for a run" },
    { id: "cycling",      icon: "🚴", label: "Cycling",      status: "fair",   message: "Light wind, manageable" },
    { id: "fishing",      icon: "🎣", label: "Fishing",      status: "poor",   message: "Poor fishing conditions" },
    { id: "stargazing",   icon: "🔭", label: "Stargazing",   status: "fair",   message: "Fair visibility tonight" },
    { id: "picnic",       icon: "🧺", label: "Picnic",       status: "good",   message: "Great day to be outside" },
    { id: "jacket",       icon: "🧥", label: "Clothing",     status: "fair",   message: "Light jacket recommended" },
    { id: "photography",  icon: "📷", label: "Photography",  status: "good",   message: "Soft light, ideal for photos" },
    { id: "gardening",    icon: "🌱", label: "Gardening",    status: "good",   message: "Good day to water plants" },
  ]
}