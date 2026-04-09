import { useState, useEffect } from 'react'
import api from '../api/axiosInstance'

function useStations() {
  const [stations, setStations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
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