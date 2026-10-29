import { useState, useEffect } from 'react'
import api from '../api/axiosInstance'

import { USE_MOCK_DATA } from '../config'
import {
  mockStation,
  // mockCurrentConditions,
  mockForecast,
  mockWeatherDetails,
  // mockLifestyle,
  mockActivities
} from '../data/mockData'

const MOCK_RESPONSE = {
  station:    mockStation,
  // conditions: mockCurrentConditions,
  forecast:   mockForecast,
  daily:      mockWeatherDetails.daily,
  widgets:    mockWeatherDetails.widgets,
  activities:  mockActivities,
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
        console.log('🟡 [MOCK] stationData:', MOCK_RESPONSE)
        setStationData(MOCK_RESPONSE)
        setLoading(false)
      }, 400)
      return
    }

    api.get(`/station-current-forecast?lat=${location.lat}&lng=${location.lng}`)
      .then(res => {
        console.log('🟢 [API] stationData:', res.data)
        setStationData(res.data)
        setLoading(false)
      })
      .catch(err => {
        console.log('🔴 [API] error:', err)
        setError(err.response?.data?.detail || err.message)
        setLoading(false)
      })
  }, [location])
    
  return { stationData, loading, error }
}

export default useStationData