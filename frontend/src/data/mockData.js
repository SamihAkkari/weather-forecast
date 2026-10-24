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
    { day: "Today", weather_code: 1,   min: 8,  max: 17 },
    { day: "Tue",   weather_code: 2,         min: 10, max: 19 },
    { day: "Wed",   weather_code: 3,         min: 6,  max: 16 },
    { day: "Thu",   weather_code: 51,         min: 12, max: 21 },
    { day: "Fri",   weather_code: 51,        min: 9,  max: 18 },
    { day: "Sat",   weather_code: 51, min: 7,  max: 17 },
  ],
  widgets: {
    humidity: {
      value: 72,
      unit: "%",
      message: "Quite humid today",
      variable_description: "Relative humidity is the amount of moisture in the air, expressed as a percentage.",
      hourly_values: [
        { time_step_fr: "2026-10-22T00:00:00+00:00", value: 71.69976806640625 },
        { time_step_fr: "2026-10-22T01:00:00+00:00", value: 74.85040283203125 },
        { time_step_fr: "2026-10-22T02:00:00+00:00", value: 75.00035095214844 },
        { time_step_fr: "2026-10-22T03:00:00+00:00", value: 76.54887390136719 },
        { time_step_fr: "2026-10-22T04:00:00+00:00", value: 79.6739501953125 },
        { time_step_fr: "2026-10-22T05:00:00+00:00", value: 79.53150939941406 },
        { time_step_fr: "2026-10-22T06:00:00+00:00", value: 80.37346649169922 },
      ],
    },
    feels_like: {
      value: 12,
      unit: "°C",
      message: "Feels colder than actual",
      variable_description: "The perceived temperature, adjusted for factors such as wind and humidity.",
      hourly_values: [
        { time_step_fr: "2026-10-22T00:00:00+00:00", value: 12.1 },
        { time_step_fr: "2026-10-22T01:00:00+00:00", value: 11.8 },
        { time_step_fr: "2026-10-22T02:00:00+00:00", value: 11.6 },
        { time_step_fr: "2026-10-22T03:00:00+00:00", value: 11.4 },
        { time_step_fr: "2026-10-22T04:00:00+00:00", value: 11.2 },
        { time_step_fr: "2026-10-22T05:00:00+00:00", value: 11.3 },
        { time_step_fr: "2026-10-22T06:00:00+00:00", value: 11.5 },
      ],
    },
    wind: {
      value: 12,
      unit: "m/s",
      message: "Northwest, gentle breeze",
      direction: "NW",
      variable_description: "Wind speed measured at the station; direction indicates where the wind is coming from.",
      hourly_values: [
        { time_step_fr: "2026-10-22T00:00:00+00:00", value: 10.8 },
        { time_step_fr: "2026-10-22T01:00:00+00:00", value: 11.2 },
        { time_step_fr: "2026-10-22T02:00:00+00:00", value: 12 },
        { time_step_fr: "2026-10-22T03:00:00+00:00", value: 12.4 },
        { time_step_fr: "2026-10-22T04:00:00+00:00", value: 12.1 },
        { time_step_fr: "2026-10-22T05:00:00+00:00", value: 11.7 },
        { time_step_fr: "2026-10-22T06:00:00+00:00", value: 11.3 },
      ],
    },
    sunrise: {
      value: "06:42",
      unit: "",
      message: "Sunset at 20:18",
      variable_description: "The local time when the sun rises; this is a daily event, not an hourly measurement.",
      hourly_values: [],
    },
    uv_index: {
      value: 3,
      unit: "",
      message: "Moderate — no protection needed",
      variable_description: "The ultraviolet index estimates the strength of the sun's UV radiation.",
      hourly_values: [
        { time_step_fr: "2026-10-22T00:00:00+00:00", value: 2.4 },
        { time_step_fr: "2026-10-22T01:00:00+00:00", value: 2.6 },
        { time_step_fr: "2026-10-22T02:00:00+00:00", value: 2.8 },
        { time_step_fr: "2026-10-22T03:00:00+00:00", value: 3 },
        { time_step_fr: "2026-10-22T04:00:00+00:00", value: 2.7 },
        { time_step_fr: "2026-10-22T05:00:00+00:00", value: 2.3 },
        { time_step_fr: "2026-10-22T06:00:00+00:00", value: 1.9 },
      ],
    },
    visibility: {
      value: 10,
      unit: "km",
      message: "Perfectly clear today",
      variable_description: "The horizontal distance at which objects can be clearly seen.",
      hourly_values: [
        { time_step_fr: "2026-10-22T00:00:00+00:00", value: 10 },
        { time_step_fr: "2026-10-22T01:00:00+00:00", value: 10 },
        { time_step_fr: "2026-10-22T02:00:00+00:00", value: 10 },
        { time_step_fr: "2026-10-22T03:00:00+00:00", value: 9.8 },
        { time_step_fr: "2026-10-22T04:00:00+00:00", value: 9.7 },
        { time_step_fr: "2026-10-22T05:00:00+00:00", value: 9.8 },
        { time_step_fr: "2026-10-22T06:00:00+00:00", value: 10 },
      ],
    },
    pressure: {
      value: 1018.1,
      unit: "hPa",
      message: "High pressure, stable weather",
      variable_description: "Atmospheric pressure at mean sea level, expressed in hectopascals.",
      hourly_values: [
        { time_step_fr: "2026-10-22T00:00:00+00:00", value: 1017.6 },
        { time_step_fr: "2026-10-22T01:00:00+00:00", value: 1017.8 },
        { time_step_fr: "2026-10-22T02:00:00+00:00", value: 1018 },
        { time_step_fr: "2026-10-22T03:00:00+00:00", value: 1018.2 },
        { time_step_fr: "2026-10-22T04:00:00+00:00", value: 1018.1 },
        { time_step_fr: "2026-10-22T05:00:00+00:00", value: 1018.3 },
        { time_step_fr: "2026-10-22T06:00:00+00:00", value: 1018.5 },
      ],
    },
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
  { time_step_fr: "2026-04-21T12:00:00", temperature_celsius: 13, precipitation_mm: 0.0, wind_speed_m_per_s: 10, humidity_percentage: 68, weather_code: 51},
  { time_step_fr: "2026-04-21T13:00:00", temperature_celsius: 14, precipitation_mm: 0.0, wind_speed_m_per_s: 11, humidity_percentage: 67, weather_code: 51},
  { time_step_fr: "2026-04-21T14:00:00", temperature_celsius: 15, precipitation_mm: 0.0, wind_speed_m_per_s: 12, humidity_percentage: 65, weather_code: 51 },
  { time_step_fr: "2026-04-21T15:00:00", temperature_celsius: 16, precipitation_mm: 0.1, wind_speed_m_per_s: 13, humidity_percentage: 64, weather_code: 51 },
  { time_step_fr: "2026-04-21T16:00:00", temperature_celsius: 15, precipitation_mm: 0.2, wind_speed_m_per_s: 14, humidity_percentage: 66, weather_code: 51 },
  { time_step_fr: "2026-04-21T17:00:00", temperature_celsius: 14, precipitation_mm: 0.5, wind_speed_m_per_s: 13, humidity_percentage: 70, weather_code: 51 },
  { time_step_fr: "2026-04-21T18:00:00", temperature_celsius: 13, precipitation_mm: 0.3, wind_speed_m_per_s: 11, humidity_percentage: 74, weather_code: 51 },
  { time_step_fr: "2026-04-21T19:00:00", temperature_celsius: 12, precipitation_mm: 0.0, wind_speed_m_per_s: 10, humidity_percentage: 75, weather_code: 51 },
  { time_step_fr: "2026-04-21T20:00:00", temperature_celsius: 11, precipitation_mm: 0.0, wind_speed_m_per_s: 9,  humidity_percentage: 76, weather_code: 51 },
  { time_step_fr: "2026-04-21T21:00:00", temperature_celsius: 10, precipitation_mm: 0.0, wind_speed_m_per_s: 8,  humidity_percentage: 78, weather_code: 51 },
  { time_step_fr: "2026-04-21T22:00:00", temperature_celsius: 10, precipitation_mm: 0.0, wind_speed_m_per_s: 8,  humidity_percentage: 79, weather_code: 51 },
  { time_step_fr: "2026-04-21T23:00:00", temperature_celsius: 9,  precipitation_mm: 0.0, wind_speed_m_per_s: 7,  humidity_percentage: 80, weather_code: 51 },
  { time_step_fr: "2026-04-22T00:00:00", temperature_celsius: 9,  precipitation_mm: 0.0, wind_speed_m_per_s: 7,  humidity_percentage: 81, weather_code: 51 },
  { time_step_fr: "2026-04-22T01:00:00", temperature_celsius: 8,  precipitation_mm: 0.0, wind_speed_m_per_s: 6,  humidity_percentage: 82, weather_code: 51 },
  { time_step_fr: "2026-04-22T02:00:00", temperature_celsius: 8,  precipitation_mm: 0.0, wind_speed_m_per_s: 6,  humidity_percentage: 83, weather_code: 51 },
  { time_step_fr: "2026-04-22T03:00:00", temperature_celsius: 7,  precipitation_mm: 0.1, wind_speed_m_per_s: 6,  humidity_percentage: 84, weather_code: 51 },
  { time_step_fr: "2026-04-22T04:00:00", temperature_celsius: 7,  precipitation_mm: 0.0, wind_speed_m_per_s: 5,  humidity_percentage: 84, weather_code: 51 },
  { time_step_fr: "2026-04-22T05:00:00", temperature_celsius: 7,  precipitation_mm: 0.0, wind_speed_m_per_s: 5,  humidity_percentage: 85, weather_code: 51 },
  { time_step_fr: "2026-04-22T06:00:00", temperature_celsius: 7,  precipitation_mm: 0.0, wind_speed_m_per_s: 5,  humidity_percentage: 85, weather_code: 51 },
  { time_step_fr: "2026-04-22T07:00:00", temperature_celsius: 8,  precipitation_mm: 0.0, wind_speed_m_per_s: 5,  humidity_percentage: 84, weather_code: 51 },
  { time_step_fr: "2026-04-22T08:00:00", temperature_celsius: 9,  precipitation_mm: 0.0, wind_speed_m_per_s: 6,  humidity_percentage: 82, weather_code: 51 },
  { time_step_fr: "2026-04-22T09:00:00", temperature_celsius: 10, precipitation_mm: 0.0, wind_speed_m_per_s: 7,  humidity_percentage: 80, weather_code: 51 },
]

// export const mockLifestyle = {
//   activities: [
//     { id: "running",      icon: "🏃", label: "Running",      status: "good",   message: "Good conditions for a run" },
//     { id: "cycling",      icon: "🚴", label: "Cycling",      status: "fair",   message: "Light wind, manageable" },
//     { id: "fishing",      icon: "🎣", label: "Fishing",      status: "poor",   message: "Poor fishing conditions" },
//     { id: "stargazing",   icon: "🔭", label: "Stargazing",   status: "fair",   message: "Fair visibility tonight" },
//     { id: "picnic",       icon: "🧺", label: "Picnic",       status: "good",   message: "Great day to be outside" },
//     { id: "jacket",       icon: "🧥", label: "Clothing",     status: "fair",   message: "Light jacket recommended" },
//     { id: "photography",  icon: "📷", label: "Photography",  status: "good",   message: "Soft light, ideal for photos" },
//     { id: "gardening",    icon: "🌱", label: "Gardening",    status: "good",   message: "Good day to water plants" },
//   ]
// }

export const mockActivities = [
  {
    id:    "cycling",
    icon:  "🚴",
    label: "Cycling",
    // Summary fields for LifestyleWidget — derived from current_status
    status:  "green",
    message: "Good conditions right now",
    current_status: {
      time:   "2026-10-20T02:00:00+00:00",
      status: "green",
      score:  0.9,
      parameters: {
        temperature: { score: 0.9, status: "green",  description: "Comfortable cycling temperature" },
        wind:        { score: 0.9, status: "green",  description: "Light wind: good cycling conditions" },
        rain:        { score: 0.9, status: "green",  description: "Dry conditions" },
        snow:        { score: 0.9, status: "green",  description: "No significant snowfall" },
      }
    },
    best_window: [
      {
        from:   "2026-10-20T03:00:00+00:00",
        to:     "2026-10-20T04:00:00+00:00",
        reason: "Calm wind · Dry · Mild temperature"
      }
    ],
    hourly: [
      {
        time:   "2026-10-20T03:00:00+00:00",
        status: "green",
        score:  0.9,
        parameters: {
          temperature: { score: 0.9, status: "green", description: "Comfortable cycling temperature" },
          wind:        { score: 0.9, status: "green", description: "Light wind: good cycling conditions" },
          rain:        { score: 0.9, status: "green", description: "Dry conditions" },
          snow:        { score: 0.9, status: "green", description: "No significant snowfall" },
        }
      },
      {
        time:   "2026-10-20T04:00:00+00:00",
        status: "green",
        score:  0.8,
        parameters: {
          temperature: { score: 0.9, status: "green", description: "Comfortable cycling temperature" },
          wind:        { score: 0.9, status: "green", description: "Light wind: good cycling conditions" },
          rain:        { score: 0.8, status: "green", description: "Dry conditions or negligible rainfall" },
          snow:        { score: 0.9, status: "green", description: "No significant snowfall" },
        }
      },
      {
        time:   "2026-10-20T05:00:00+00:00",
        status: "yellow",
        score:  0.4,
        parameters: {
          temperature: { score: 0.9, status: "green",  description: "Comfortable cycling temperature" },
          wind:        { score: 0.9, status: "green",  description: "Light wind: good cycling conditions" },
          rain:        { score: 0.4, status: "yellow", description: "Rain: reduced grip and longer braking distances" },
          snow:        { score: 0.9, status: "green",  description: "No significant snowfall" },
        }
      },
      {
        time:   "2026-10-20T06:00:00+00:00",
        status: "yellow",
        score:  0.4,
        parameters: {
          temperature: { score: 0.9, status: "green",  description: "Comfortable cycling temperature" },
          wind:        { score: 0.9, status: "green",  description: "Light wind: good cycling conditions" },
          rain:        { score: 0.4, status: "yellow", description: "Rain: reduced grip and longer braking distances" },
          snow:        { score: 0.9, status: "green",  description: "No significant snowfall" },
        }
      },
      {
        time:   "2026-10-20T07:00:00+00:00",
        status: "yellow",
        score:  0.4,
        parameters: {
          temperature: { score: 0.9, status: "green",  description: "Comfortable cycling temperature" },
          wind:        { score: 0.9, status: "green",  description: "Light wind: good cycling conditions" },
          rain:        { score: 0.4, status: "yellow", description: "Rain: reduced grip and longer braking distances" },
          snow:        { score: 0.9, status: "green",  description: "No significant snowfall" },
        }
      },
    ]
  },
  {
    id:    "running",
    icon:  "🏃",
    label: "Running",
    status:  "green",
    message: "Perfect conditions for a run",
    current_status: {
      time:   "2026-10-20T02:00:00+00:00",
      status: "green",
      score:  0.9,
      parameters: {
        temperature: { score: 0.9, status: "green", description: "Cool and comfortable for running" },
        wind:        { score: 0.9, status: "green", description: "Light wind" },
        rain:        { score: 0.9, status: "green", description: "Dry conditions" },
      }
    },
    best_window: [
      { from: "2026-10-20T07:00:00+00:00", to: "2026-10-20T09:00:00+00:00", reason: "Cool and dry — ideal for running" }
    ],
    hourly: [
      { time: "2026-10-20T07:00:00+00:00", status: "green",  score: 1.0, parameters: { temperature: { score: 1.0, status: "green",  description: "Perfect running temperature" }, wind: { score: 0.9, status: "green", description: "Light wind" }, rain: { score: 1.0, status: "green", description: "Dry" } } },
      { time: "2026-10-20T08:00:00+00:00", status: "green",  score: 0.9, parameters: { temperature: { score: 0.9, status: "green",  description: "Good temperature" },            wind: { score: 0.9, status: "green", description: "Light wind" }, rain: { score: 1.0, status: "green", description: "Dry" } } },
      { time: "2026-10-20T13:00:00+00:00", status: "yellow", score: 0.6, parameters: { temperature: { score: 0.6, status: "yellow", description: "Getting warm for running" },      wind: { score: 0.9, status: "green", description: "Light wind" }, rain: { score: 1.0, status: "green", description: "Dry" } } },
      { time: "2026-10-20T15:00:00+00:00", status: "yellow", score: 0.4, parameters: { temperature: { score: 0.9, status: "green",  description: "Good temperature" },            wind: { score: 0.9, status: "green", description: "Light wind" }, rain: { score: 0.4, status: "yellow", description: "Light rain" } } },
    ]
  },
  {
    id:    "fishing",
    icon:  "🎣",
    label: "Fishing",
    status:  "yellow",
    message: "Moderate wind — check conditions",
    current_status: {
      time:   "2026-10-20T02:00:00+00:00",
      status: "yellow",
      score:  0.6,
      parameters: {
        wind: { score: 0.6, status: "yellow", description: "Moderate wind — fishing possible but not ideal" },
        rain: { score: 0.8, status: "green",  description: "Light rain — fish may be active" },
      }
    },
    best_window: [
      { from: "2026-10-20T06:00:00+00:00", to: "2026-10-20T09:00:00+00:00", reason: "Calm morning · Overcast — fish feed well" }
    ],
    hourly: [
      { time: "2026-10-20T06:00:00+00:00", status: "green",  score: 0.9, parameters: { wind: { score: 0.9, status: "green",  description: "Calm — ideal fishing conditions" }, rain: { score: 0.9, status: "green", description: "Dry" } } },
      { time: "2026-10-20T10:00:00+00:00", status: "yellow", score: 0.5, parameters: { wind: { score: 0.5, status: "yellow", description: "Moderate wind picking up" },          rain: { score: 0.9, status: "green", description: "Dry" } } },
      { time: "2026-10-20T14:00:00+00:00", status: "red",    score: 0.2, parameters: { wind: { score: 0.2, status: "red",    description: "Too windy for fishing" },             rain: { score: 0.4, status: "yellow", description: "Rain making conditions worse" } } },
    ]
  },
  {
    id:    "stargazing",
    icon:  "🔭",
    label: "Stargazing",
    status:  "red",
    message: "Heavy cloud cover tonight",
    current_status: {
      time:   "2026-10-20T02:00:00+00:00",
      status: "red",
      score:  0.2,
      parameters: {
        cloud:    { score: 0.2, status: "red",   description: "Heavy overcast — no visibility" },
        humidity: { score: 0.5, status: "yellow", description: "High humidity reduces clarity" },
      }
    },
    best_window: [],
    hourly: [
      { time: "2026-10-20T21:00:00+00:00", status: "red",    score: 0.2, parameters: { cloud: { score: 0.2, status: "red",   description: "Overcast" },         humidity: { score: 0.5, status: "yellow", description: "High humidity" } } },
      { time: "2026-10-20T22:00:00+00:00", status: "red",    score: 0.2, parameters: { cloud: { score: 0.2, status: "red",   description: "Overcast" },         humidity: { score: 0.5, status: "yellow", description: "High humidity" } } },
      { time: "2026-10-20T23:00:00+00:00", status: "yellow", score: 0.5, parameters: { cloud: { score: 0.5, status: "yellow", description: "Partial clearing" }, humidity: { score: 0.6, status: "yellow", description: "Humidity dropping" } } },
      { time: "2026-10-21T00:00:00+00:00", status: "green",  score: 0.8, parameters: { cloud: { score: 0.8, status: "green", description: "Mostly clear" },      humidity: { score: 0.8, status: "green",  description: "Good visibility" } } },
    ]
  },
  {
    id:    "picnic",
    icon:  "🧺",
    label: "Picnic",
    status:  "green",
    message: "Great weather for a picnic",
    current_status: {
      time:   "2026-10-20T02:00:00+00:00",
      status: "green",
      score:  0.9,
      parameters: {
        temperature: { score: 0.9, status: "green", description: "Warm and pleasant" },
        wind:        { score: 0.9, status: "green", description: "Light breeze" },
        rain:        { score: 1.0, status: "green", description: "No rain expected" },
      }
    },
    best_window: [
      { from: "2026-10-20T11:00:00+00:00", to: "2026-10-20T15:00:00+00:00", reason: "Warm and sunny — perfect picnic window" }
    ],
    hourly: [
      { time: "2026-10-20T11:00:00+00:00", status: "green",  score: 1.0, parameters: { temperature: { score: 1.0, status: "green", description: "Perfect picnic temperature" }, wind: { score: 0.9, status: "green", description: "Light breeze" }, rain: { score: 1.0, status: "green", description: "Dry" } } },
      { time: "2026-10-20T14:00:00+00:00", status: "green",  score: 0.9, parameters: { temperature: { score: 0.9, status: "green", description: "Still warm" },                wind: { score: 0.9, status: "green", description: "Light breeze" }, rain: { score: 1.0, status: "green", description: "Dry" } } },
      { time: "2026-10-20T16:00:00+00:00", status: "yellow", score: 0.5, parameters: { temperature: { score: 0.9, status: "green", description: "Cooling down" },               wind: { score: 0.9, status: "green", description: "Light breeze" }, rain: { score: 0.5, status: "yellow", description: "Light rain risk" } } },
    ]
  },
  {
    id:    "jacket",
    icon:  "🧥",
    label: "Clothing",
    status:  "yellow",
    message: "Light jacket recommended",
    current_status: {
      time:   "2026-10-20T02:00:00+00:00",
      status: "yellow",
      score:  0.6,
      parameters: {
        temperature: { score: 0.6, status: "yellow", description: "14°C — jacket recommended" },
        wind:        { score: 0.8, status: "green",  description: "Light wind" },
        rain:        { score: 0.9, status: "green",  description: "Dry" },
      }
    },
    best_window: [],
    hourly: [
      { time: "2026-10-20T09:00:00+00:00", status: "green",  score: 0.9, parameters: { temperature: { score: 0.9, status: "green",  description: "Comfortable — no jacket needed" }, wind: { score: 0.9, status: "green", description: "Calm" } } },
      { time: "2026-10-20T14:00:00+00:00", status: "green",  score: 1.0, parameters: { temperature: { score: 1.0, status: "green",  description: "Warm — T-shirt weather" },          wind: { score: 0.9, status: "green", description: "Calm" } } },
      { time: "2026-10-20T18:00:00+00:00", status: "yellow", score: 0.6, parameters: { temperature: { score: 0.6, status: "yellow", description: "Cooling — light jacket useful" },    wind: { score: 0.7, status: "green", description: "Light wind" } } },
      { time: "2026-10-20T21:00:00+00:00", status: "red",    score: 0.3, parameters: { temperature: { score: 0.3, status: "red",    description: "Cold — warm jacket needed" },         wind: { score: 0.5, status: "yellow", description: "Cool wind" } } },
    ]
  },
  {
    id:    "photography",
    icon:  "📷",
    label: "Photography",
    status:  "green",
    message: "Soft light — ideal for photos",
    current_status: {
      time:   "2026-10-20T02:00:00+00:00",
      status: "green",
      score:  0.9,
      parameters: {
        cloud: { score: 0.8, status: "green", description: "Overcast — soft diffused light" },
        rain:  { score: 1.0, status: "green", description: "No rain — equipment safe" },
      }
    },
    best_window: [
      { from: "2026-10-20T07:00:00+00:00", to: "2026-10-20T09:00:00+00:00", reason: "Golden hour · Low angle warm light" },
      { from: "2026-10-20T18:00:00+00:00", to: "2026-10-20T20:00:00+00:00", reason: "Golden hour evening" }
    ],
    hourly: [
      { time: "2026-10-20T07:00:00+00:00", status: "green",  score: 1.0, parameters: { cloud: { score: 1.0, status: "green", description: "Golden hour" },          rain: { score: 1.0, status: "green", description: "Dry" } } },
      { time: "2026-10-20T12:00:00+00:00", status: "yellow", score: 0.6, parameters: { cloud: { score: 0.6, status: "yellow", description: "Harsh midday light" },  rain: { score: 1.0, status: "green", description: "Dry" } } },
      { time: "2026-10-20T15:00:00+00:00", status: "red",    score: 0.2, parameters: { cloud: { score: 0.9, status: "green",  description: "Soft light" },          rain: { score: 0.2, status: "red",   description: "Rain — equipment risk" } } },
      { time: "2026-10-20T18:00:00+00:00", status: "green",  score: 1.0, parameters: { cloud: { score: 1.0, status: "green",  description: "Golden hour evening" }, rain: { score: 1.0, status: "green", description: "Dry" } } },
    ]
  },
  {
    id:    "gardening",
    icon:  "🌱",
    label: "Gardening",
    status:  "green",
    message: "Good day to garden",
    current_status: {
      time:   "2026-10-20T02:00:00+00:00",
      status: "green",
      score:  0.9,
      parameters: {
        temperature: { score: 0.9, status: "green", description: "Mild and comfortable" },
        rain:        { score: 0.9, status: "green", description: "Dry — good for digging" },
        wind:        { score: 0.9, status: "green", description: "Light breeze" },
      }
    },
    best_window: [
      { from: "2026-10-20T09:00:00+00:00", to: "2026-10-20T12:00:00+00:00", reason: "Cool and dry — ideal for gardening" }
    ],
    hourly: [
      { time: "2026-10-20T09:00:00+00:00", status: "green",  score: 1.0, parameters: { temperature: { score: 1.0, status: "green", description: "Perfect gardening temperature" }, rain: { score: 1.0, status: "green", description: "Dry" }, wind: { score: 0.9, status: "green", description: "Calm" } } },
      { time: "2026-10-20T14:00:00+00:00", status: "yellow", score: 0.6, parameters: { temperature: { score: 0.6, status: "yellow", description: "Getting warm" },                  rain: { score: 1.0, status: "green", description: "Dry" }, wind: { score: 0.9, status: "green", description: "Calm" } } },
      { time: "2026-10-20T16:00:00+00:00", status: "red",    score: 0.2, parameters: { temperature: { score: 0.9, status: "green",  description: "Good temperature" },               rain: { score: 0.2, status: "red",   description: "Heavy rain" }, wind: { score: 0.9, status: "green", description: "Calm" } } },
      { time: "2026-10-20T18:00:00+00:00", status: "green",  score: 0.9, parameters: { temperature: { score: 0.9, status: "green",  description: "Mild evening" },                   rain: { score: 1.0, status: "green", description: "Rain stopped" }, wind: { score: 0.9, status: "green", description: "Calm" } } },
    ]
  },
]


export const mockPvProduction = {
  system: {
    capacity_kw: 3.0,
    tilt: 30,
    azimuth: 180,
    losses_pct: 14.0,
    inverter_capacity_kw: 2.5,
    inverter_efficiency: 0.96,
  },
  hourly: [
    { time: '2026-10-22T10:00:00', power_w: 1240.5, energy_wh: 1240.5, ghi_wm2: 380.2, poa_wm2: 420.1 },
    { time: '2026-10-22T11:00:00', power_w: 1640.0, energy_wh: 1640.0, ghi_wm2: 470.0, poa_wm2: 520.3 },
    { time: '2026-10-22T12:00:00', power_w: 2050.7, energy_wh: 2050.7, ghi_wm2: 560.4, poa_wm2: 610.8 },
    { time: '2026-10-22T13:00:00', power_w: 2180.3, energy_wh: 2180.3, ghi_wm2: 590.1, poa_wm2: 645.2 },
    { time: '2026-10-22T14:00:00', power_w: 1710.2, energy_wh: 1710.2, ghi_wm2: 480.6, poa_wm2: 530.9 },
  ],
  total_energy_kwh: 8.82,
  peak_power_w: 2180.3,
  peak_hour: '2026-10-22T13:00:00',
  energy_period_message: "over 5 forecast hours",
  energy_clipping_percent: 0, 
  clipping_message: '✓ No clipping detected',
  insight_message: 'insight'

}