import { useNavigate } from '../../router-compat'

const STATUS_CONFIG = {
  green:  { bg: 'bg-success/15', label: 'Good' },
  yellow: { bg: 'bg-warning/15', label: 'Fair' },
  red:    { bg: 'bg-destructive/15', label: 'Poor' },
}

const STATUS_COLORS = {
  dark_green: '#166534',
  green: '#16a34a',
  light_green: '#4ade80',
  yellow_green: '#a3e635',
  yellow: '#facc15',
  yellow_orange: '#fbbf24',
  orange: '#f97316',
  dark_orange: '#ea580c',
  red: '#ef4444',
  dark_red: '#991b1b',
}

const STATUS_QUALITY = {
  dark_green: 'green',
  green: 'green',
  light_green: 'green',
  yellow_green: 'yellow',
  yellow: 'yellow',
  yellow_orange: 'yellow',
  orange: 'red',
  dark_orange: 'red',
  red: 'red',
  dark_red: 'red',
}

function LifestyleWidget({ activities }) {
  const navigate = useNavigate()

  return (
    <div>
      <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-primary mb-4">🌿 Lifestyle & activities</p>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {activities.map(activity => {
          const quality = STATUS_QUALITY[activity.status] ?? 'yellow'
          const config = STATUS_CONFIG[quality]

          return (
            <div
              key={activity.id}
              onClick={() => navigate(`/activity/${activity.id}`, {
                state: { activities }
              })}
              className={`glass border border-border rounded-2xl p-3 cursor-pointer lift transition-colors group ${config.bg}`}
            >
              {/* Header row: icon + label + status dot */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <span className="text-base">{activity.icon}</span>
                  <span className="text-xs font-medium text-foreground group-hover:text-foreground transition-colors">
                    {activity.label}
                  </span>
                </div>
                <div
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ background: STATUS_COLORS[activity.status] ?? '#facc15' }}
                />
              </div>

              {/* Message */}
              <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                {activity.message}
              </p>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-3 pt-3 border-t border-border">
        {Object.entries(STATUS_CONFIG).map(([key, config]) => (
          <div key={key} className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: STATUS_COLORS[key] }} />
            <span className="text-xs text-subtle">{config.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default LifestyleWidget