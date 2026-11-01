import { useParams, useNavigate } from '../router-compat'
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
    <div className="min-h-screen">
      <Navbar />

      <div className="max-w-5xl mx-auto px-6 py-10 animate-rise">

        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-muted-foreground hover:text-primary transition-colors inline-flex items-center gap-1 rounded-full border border-border px-3 py-1.5 glass"
          >
            ← Back
          </button>
          {activityData && (
            <h1 className="text-2xl sm:text-3xl font-semibold text-foreground">
              {activityData.icon} {activityData.label}
            </h1>
          )}
        </div>

        {loading && (
          <div className="text-center py-20 text-muted-foreground text-sm">
            Loading...
          </div>
        )}

        {error && !loading && (
          <div className="text-center py-20 text-muted-foreground text-sm">
            {error}{' '}
            <button onClick={() => navigate(-1)} className="text-primary">
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
    <p className="text-xs text-subtle mt-6">
      Advice is indicative and based on forecasts. Always check official Météo-France warnings
      (vigilance) before outdoor activities.
    </p>
    
    </div>
  )
}

export default ActivityPage