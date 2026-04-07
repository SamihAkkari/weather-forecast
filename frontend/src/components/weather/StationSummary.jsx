
function StationSummary({ station, conditions }) {
  return (
    <div className="border border-gray-100 rounded-xl p-5 h-full">
      <p className="text-xs text-gray-400 mb-1">Selected station</p>
      <p className="text-base font-medium text-gray-900 mb-4">{station.name}</p>

      <div className="grid grid-cols-2 gap-2">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Temperature</p>
          <p className="text-2xl font-medium text-gray-900">{conditions.temperature}°C</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Humidity</p>
          <p className="text-2xl font-medium text-gray-900">{conditions.humidity}%</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Wind</p>
          <p className="text-2xl font-medium text-gray-900">{conditions.windSpeed} m/s</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Rain</p>
          <p className="text-2xl font-medium text-gray-900">{conditions.precipitation} mm</p>
        </div>
      </div>
    </div>
  );
}

export default StationSummary