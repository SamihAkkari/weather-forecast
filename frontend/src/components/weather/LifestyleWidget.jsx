import { useNavigate } from 'react-router-dom'

// Replace STATUS_CONFIG / STATUS_STYLES / BAR_COLORS everywhere with:
const STATUS_CONFIG = {
  green:  { color: '#4ade80', label: 'Good'  },
  yellow: { color: '#facc15', label: 'Fair'  },
  red:    { color: '#f87171', label: 'Poor'  },
}

function LifestyleWidget({ activities }) {
  const navigate = useNavigate()

  return (
    <div className="border border-gray-100 rounded-xl p-4 bg-white">
      <p className="text-xs text-gray-400 mb-4">🌿 Lifestyle & activities</p>

      <div className="grid grid-cols-2 gap-x-4 gap-y-3">
        {activities.map(activity => {
          const config = STATUS_CONFIG[activity.status] ?? STATUS_CONFIG.fair

          return (
            <div
              key={activity.id}
              onClick={() => navigate(`/activity/${activity.id}`, {

                state: { activities }
              })}
              className="flex items-start gap-2.5 cursor-pointer group"
            >
              <div
                className="w-2 h-2 rounded-full mt-1 flex-shrink-0"
                style={{ background: config.color }}
              />
              <div className="min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className="text-sm">{activity.icon}</span>
                  <span className="text-xs font-medium text-gray-700 group-hover:text-gray-900 transition-colors">
                    {activity.label}
                  </span>
                </div>
                {/* <p className="text-xs text-gray-400 leading-relaxed">
                  {activity.message}
                </p> */}
              </div>
            </div>
          )
        })}
      </div>

      <div className="flex gap-4 mt-4 pt-3 border-t border-gray-50">
        {Object.entries(STATUS_CONFIG).map(([key, config]) => (
          <div key={key} className="flex items-center gap-1.5">
            <div
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ background: config.color }}
            />
            <span className="text-xs text-gray-300">{config.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default LifestyleWidget