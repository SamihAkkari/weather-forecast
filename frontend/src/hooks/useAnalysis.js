import { useState } from 'react'
import api from '../api/axiosInstance'
import { mockAnalysis } from '../data/mockData'

export function useAnalysis() {
    const [analysisData, setAnalysisData] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    async function runAnalysis(lat, lng, days) {
        setLoading(true)
        setError(null)
        setAnalysisData(null)

        try {
          const res = await api.get('/analysis', {
            params: { lat, lng, days }
          })
          setAnalysisData(res.data)
        } catch (err) {
          setError(
            err.response?.data?.detail || 'No data found for this location and period.'
          )
        } finally {
          setLoading(false)
        }
        // setTimeout(() => {
        //     setAnalysisData(mockAnalysis)
        //     setLoading(false)
        // }, 500)
}

return { analysisData, loading, error, runAnalysis }
}