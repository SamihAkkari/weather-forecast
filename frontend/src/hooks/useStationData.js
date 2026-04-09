import { useState, useEffect } from 'react'
import api from '../api/axiosInstance'

function useStationData(stationId) {
  const [stationData, setStationData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!stationId) return

    setLoading(true)
    setStationData(null)

    api.get(`/station-current-forecast/${stationId}`)
      .then(res => {
        setStationData(res.data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [stationId])

  return { stationData, loading, error }
}

export default useStationData