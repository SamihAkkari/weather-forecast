import { useNavigate } from 'react-router-dom'

const STATUS_CONFIG = {
  green:  { color: '#4ade80', bg: 'bg-green-50',  label: 'Good' },
  yellow: { color: '#facc15', bg: 'bg-yellow-50', label: 'Fair' },
  red:    { color: '#f87171', bg: 'bg-red-50',    label: 'Poor' },
}

function LifestyleWidget({ activities }) {
  const navigate = useNavigate()

  return (
    <div className="bg-white">
      <p className="text-xs text-gray-400 mb-3">🌿 Lifestyle & activities</p>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {activities.map(activity => {
          const config = STATUS_CONFIG[activity.status] ?? STATUS_CONFIG.yellow

          return (
            <div
              key={activity.id}
              onClick={() => navigate(`/activity/${activity.id}`, {
                state: { activities }
              })}
              className="border border-gray-100 rounded-xl p-3 cursor-pointer hover:border-gray-300 transition-colors group"
            >
              {/* Header row: icon + label + status dot */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <span className="text-base">{activity.icon}</span>
                  <span className="text-xs font-medium text-gray-700 group-hover:text-gray-900 transition-colors">
                    {activity.label}
                  </span>
                </div>
                <div
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ background: config.color }}
                />
              </div>

              {/* Message */}
              <p className="text-xs text-gray-400 leading-relaxed line-clamp-2">
                {activity.message}
              </p>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-3 pt-3 border-t border-gray-50">
        {Object.entries(STATUS_CONFIG).map(([key, config]) => (
          <div key={key} className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: config.color }} />
            <span className="text-xs text-gray-300">{config.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default LifestyleWidget