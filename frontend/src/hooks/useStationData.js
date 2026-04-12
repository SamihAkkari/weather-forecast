import { useState, useEffect } from 'react'
import api from '../api/axiosInstance'

function useStationData(location) {
  const [stationData, setStationData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!location) return

    setLoading(true)
    setStationData(null)

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