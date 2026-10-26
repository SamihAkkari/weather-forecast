function ConfusionMatrix({ tp, fp, fn, tn }) {
  return (
    <div>
      <div className="grid grid-cols-2 gap-1 mb-1">
        <p className="text-xs text-gray-300 text-center">Predicted rain</p>
        <p className="text-xs text-gray-300 text-center">Predicted dry</p>
      </div>
      <div className="grid grid-cols-2 gap-1">
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-400 mb-1">True positive</p>
          <p className="text-xl font-medium text-blue-700">{tp}</p>
        </div>
        <div className="bg-red-50 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-400 mb-1">False negative</p>
          <p className="text-xl font-medium text-red-400">{fn}</p>
        </div>
        <div className="bg-red-50 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-400 mb-1">False positive</p>
          <p className="text-xl font-medium text-red-400">{fp}</p>
        </div>
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-400 mb-1">True negative</p>
          <p className="text-xl font-medium text-blue-700">{tn}</p>
        </div>
      </div>
    </div>
  )
}

function MetricBar({ label, percent }) {
  const display = percent
  const color =
    display >= 80 ? 'bg-green-400' :
    display >= 60 ? 'bg-yellow-400' :
    'bg-red-400'

  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-xs font-medium text-gray-700">{display}%</p>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full ${color}`}
          style={{ width: `${display}%` }}
        />
      </div>
    </div>
  )
}

function DetectionAnalysis({ data }) {
  return (
    <div>
      <p className="text-xs text-gray-400 mb-4">
        Confusion matrix: summed across all runs and stations in the period
      </p>

      <div className="grid grid-cols-2 gap-6 mb-4">
        <ConfusionMatrix
          tp={data.tp} fp={data.fp}
          fn={data.fn} tn={data.tn}
        />
        <div className="flex flex-col justify-center gap-4">
          <MetricBar label="Precision" percent={data.precision} />
          <MetricBar label="Recall"    percent={data.recall}    />
          <MetricBar label="F1 score"  percent={data.f1}        />
        </div>
      </div>

      <div className="px-3 py-2.5 bg-blue-50 rounded-lg">
        <p className="text-xs text-blue-700">💡 {data.insight}</p>
      </div>
    </div>
  )
}

export default DetectionAnalysis