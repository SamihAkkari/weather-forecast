import { useState, useEffect } from 'react'
import api from '../api/axiosInstance'
import { USE_MOCK_DATA } from '../config'
import { mockStation } from '../data/mockData'

function useStations() {
  const [stations, setStations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (USE_MOCK_DATA) {
      setStations([{ ...mockStation, lat: mockStation.latitude, lng: mockStation.longitude }])
      setLoading(false)
      return
    }
    api.get('/stations')
      .then(res => {
        setStations(res.data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  return { stations, loading, error }
}

export default useStations