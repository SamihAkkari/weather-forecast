
function ValueWithUnit({ value, unit, format }) {
  if (value === null || value === undefined) {
    return (
      <span className="text-sm text-gray-400 italic">
        No data provided
      </span>
    );
  }

  return (
    <>
      {format(value)}
      {unit}
    </>
  );
}

function StationSummary({ station_info, conditions }) {
  return (
    <div className="border border-gray-100 rounded-xl p-5 h-full">
      <p className="text-xs text-gray-400 mb-1">Selected station</p>
      <p className="text-base font-medium text-gray-900 mb-4">{station_info.location_name}</p>

      <div className="grid grid-cols-2 gap-2">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Temperature</p>
          <p className="text-2xl font-medium text-gray-900">
            <ValueWithUnit
              value={conditions.temperature_celsius}
              unit="°C"
              format={(v) => Math.floor(v)}
            />
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Humidity</p>
          <p className="text-2xl font-medium text-gray-900">
            <ValueWithUnit
              value={conditions.humidity_percentage}
              unit="%"
              format={(v) => Math.floor(v)}
            />
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Wind</p>
          <p className="text-2xl font-medium text-gray-900">
            <ValueWithUnit
              value={conditions.wind_speed_m_per_s}
              unit=" m/s"
              format={(v) => v.toFixed(1)}
            />
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Rain</p>
          <p className="text-2xl font-medium text-gray-900">
            <ValueWithUnit
              value={conditions.precipitation_mm}
              unit=" mm"
              format={(v) => v.toFixed(2)}
            />
          </p>
        </div>
      </div>
    </div>
  );
}

export default StationSummary