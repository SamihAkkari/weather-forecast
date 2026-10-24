import { useState } from 'react'
import api from '../api/axiosInstance'
import { USE_MOCK_DATA } from '../config'
import { mockPvProduction } from '../data/mockData'

export function usePvProduction() {
  const [pvData, setPvData]     = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  async function compute(location, system) {
    if (!location) return

    setLoading(true)
    setError(null)
    setPvData(null)

    if (USE_MOCK_DATA) {
      setTimeout(() => {
        setPvData(mockPvProduction)
        setLoading(false)
      }, 400)
      return
    }

    try {
      const res = await api.get('/pv-production', {
        params: {
          lat:                 location.lat,
          lng:                 location.lng,
          system_capacity_kw:  system.capacity_kw,
          tilt:                system.tilt,
          azimuth:             system.azimuth,
          losses_pct:          system.losses_pct,
          inverter_capacity_kw: system.inverter_capacity_kw,
        }
      })
      console.log('🟢 [API] PvProduction:', res.data)
      setPvData(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to compute PV production.')
    } finally {
      setLoading(false)
    }
  }

  return { pvData, loading, error, compute }
}