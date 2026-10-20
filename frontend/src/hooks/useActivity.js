import { useLocation } from 'react-router-dom'

export function useActivity(id) {

  const location = useLocation()
  const activities = location.state?.activities

  if (!activities) {
    return {
      activityData: null,
      loading: false,
      error: 'Please navigate here from the weather viewer.'
    }
  }

  const activityData = activities.find(a => a.id === id) ?? null

  return {
    activityData,
    loading: false,
    error: activityData ? null : 'Activity not found.'
  }
}