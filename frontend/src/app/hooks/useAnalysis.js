import { useState } from "react";
import api from "../api/axiosInstance";
import { USE_MOCK_DATA } from "../config";
import { mockAnalysis } from "../data/mockData";

export function useAnalysis() {
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function runAnalysis(lat, lng, days) {
    setLoading(true);
    setError(null);
    setAnalysisData(null);

    if (USE_MOCK_DATA) {
      setTimeout(() => {
        setAnalysisData(mockAnalysis);
        setLoading(false);
      }, 400);
      return;
    }

    try {
      const params = { days };
      /*
        lat and lng are optional   if null we omit them
        and the backend aggregates over all stations.
      */
      if (lat !== null && lng !== null) {
        params.lat = lat;
        params.lng = lng;
      }
      const res = await api.get("/analysis", { params });
      setAnalysisData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load analysis.");
    } finally {
      setLoading(false);
    }
  }

  return { analysisData, loading, error, runAnalysis };
}
