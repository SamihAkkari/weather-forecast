import { useParams, useNavigate } from 'react-router-dom'
import Navbar from '../components/common/Navbar'
import CurrentStatus from '../components/activity/CurrentStatus'
import BestWindows from '../components/activity/BestWindows'
import HourlyTimeline from '../components/activity/HourlyTimeline'
import { useActivity } from '../hooks/useActivity'

function ActivityPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { activityData, loading, error } = useActivity(id)

  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      <div className="max-w-3xl mx-auto px-8 py-8">

        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
          >
            ← Back
          </button>
          {activityData && (
            <h1 className="text-lg font-medium text-gray-900">
              {activityData.icon} {activityData.label}
            </h1>
          )}
        </div>

        {loading && (
          <div className="text-center py-20 text-gray-400 text-sm">
            Loading...
          </div>
        )}

        {error && !loading && (
          <div className="text-center py-20 text-gray-400 text-sm">
            {error}{' '}
            <button onClick={() => navigate(-1)} className="text-blue-500">
              Go back
            </button>
          </div>
        )}

        {activityData && !loading && (
          <>
            <CurrentStatus current_status={activityData.current_status} />
            <BestWindows best_window={activityData.best_window} />
            <HourlyTimeline hourly={activityData.hourly} />
          </>
        )}

      </div>
    <p className="text-xs text-gray-300 mt-6">
      Advice is indicative and based on forecasts. Always check official Météo-France warnings
      (vigilance) before outdoor activities.
    </p>
    
    </div>
  )
}

export default ActivityPage