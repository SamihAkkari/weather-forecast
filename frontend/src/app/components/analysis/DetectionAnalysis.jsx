function ConfusionMatrix({ tp, fp, fn, tn }) {
  return (
    <div>
      <div className="grid grid-cols-2 gap-1 mb-1">
        <p className="text-xs text-subtle text-center">Predicted rain</p>
        <p className="text-xs text-subtle text-center">Predicted dry</p>
      </div>
      <div className="grid grid-cols-2 gap-1">
        <div className="bg-info/15 rounded-lg p-3 text-center">
          <p className="text-xs text-muted-foreground mb-1">True positive</p>
          <p className="text-xl font-medium text-primary">{tp}</p>
        </div>
        <div className="bg-destructive/15 rounded-lg p-3 text-center">
          <p className="text-xs text-muted-foreground mb-1">False negative</p>
          <p className="text-xl font-medium text-destructive">{fn}</p>
        </div>
        <div className="bg-destructive/15 rounded-lg p-3 text-center">
          <p className="text-xs text-muted-foreground mb-1">False positive</p>
          <p className="text-xl font-medium text-destructive">{fp}</p>
        </div>
        <div className="bg-info/15 rounded-lg p-3 text-center">
          <p className="text-xs text-muted-foreground mb-1">True negative</p>
          <p className="text-xl font-medium text-primary">{tn}</p>
        </div>
      </div>
    </div>
  )
}

function MetricBar({ label, percent }) {
  const isMissing = percent == null || Number.isNaN(percent)

  const color =
    percent >= 80 ? 'bg-success' :
    percent >= 60 ? 'bg-warning' :
    'bg-destructive'

  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-xs font-medium text-foreground">
          {isMissing ? 'N/A' : `${percent}%`}
        </p>
      </div>

      <div className="w-full bg-muted rounded-full h-1.5">
        {!isMissing && (
          <div
            className={`h-1.5 rounded-full ${color}`}
            style={{ width: `${percent}%` }}
          />
        )}
      </div>
    </div>
  )
}

function DetectionAnalysis({ data }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground mb-4">
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
          <MetricBar label="Specificity"  percent={data.specificity}        />
          <MetricBar label="Balanced accuracy"  percent={data.balanced_acc}        />
          <MetricBar label="Accuracy"  percent={data.accuracy}        />
        </div>
      </div>

      <div className="px-3 py-2.5 bg-info/15 rounded-lg">
        <p className="text-xs text-primary">💡 {data.insight}</p>
      </div>
    </div>
  )
}

export default DetectionAnalysis