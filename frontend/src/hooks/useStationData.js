import { useState, useEffect } from 'react'
import api from '../api/axiosInstance'

import { USE_MOCK_DATA } from '../config'
import {
  mockStation,
  mockCurrentConditions,
  mockForecast,
  mockWeatherDetails,
  mockLifestyle
} from '../data/mockData'

const MOCK_RESPONSE = {
  station:    mockStation,
  conditions: mockCurrentConditions,
  forecast:   mockForecast,
  daily:      mockWeatherDetails.daily,
  widgets:    mockWeatherDetails.widgets,
  lifestyle:  mockLifestyle,
}

function useStationData(location) {
  const [stationData, setStationData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!location) return

    setLoading(true)
    setStationData(null)
    setError(null)

    if (USE_MOCK_DATA) {
      setTimeout(() => {
        setStationData(MOCK_RESPONSE)
        setLoading(false)
      }, 400)
      return
    }

    api.get(`/station-current-forecast?lat=${location.lat}&lng=${location.lng}`)
      .then(res => {
        setStationData(res.data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [location])

  return { stationData, loading, error }
}

export default useStationData