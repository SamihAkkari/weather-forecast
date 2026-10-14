/*
  LifestyleWidget shows a single card containing all lifestyle activities.
  Each activity has a status: good, fair, or poor.
  The status drives the color of the indicator dot next to each item.

  We keep all activities in one card rather than one card per activity
  because there are many of them and individual cards would make the
  page feel very heavy. A compact list inside one card works better.
*/

/*
  Status config maps each status value to a color and a label.
  Centralizing this here means if you add a new status level later
  you only change it in one place.
*/
const STATUS_CONFIG = {
  good: { color: '#4ade80', label: 'Good' },
  fair: { color: '#fbbf24', label: 'Fair' },
  poor: { color: '#f87171', label: 'Poor' },
}

function LifestyleWidget({ activities }) {
  return (
    <div className="border border-gray-100 rounded-xl p-4 bg-white">

      <p className="text-xs text-gray-400 mb-4">🌿 Lifestyle & activities</p>

      <div className="grid grid-cols-2 gap-x-4 gap-y-3">
        {activities.map(activity => {
          const config = STATUS_CONFIG[activity.status] ?? STATUS_CONFIG.fair

          return (
            <div key={activity.id} className="flex items-start gap-2.5">

              {/* Status dot — color encodes good/fair/poor at a glance */}
              <div
                className="w-2 h-2 rounded-full mt-1 flex-shrink-0"
                style={{ background: config.color }}
              />

              <div className="min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className="text-sm">{activity.icon}</span>
                  <span className="text-xs font-medium text-gray-700">
                    {activity.label}
                  </span>
                </div>
                <p className="text-xs text-gray-400 leading-relaxed">
                  {activity.message}
                </p>
              </div>

            </div>
          )
        })}
      </div>

      {/* Legend at the bottom so the user understands the dot colors */}
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