import DegradationChart from './DegradationChart'

function MetricCard({ label, value, unit }) {
  return (
    <div className="bg-muted rounded-lg p-3">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="text-lg font-medium text-foreground">
        {value !== null ? `${value}` : '—'}
        <span className="text-sm font-normal text-muted-foreground ml-0.5">{unit}</span>
      </p>
    </div>
  )
}

function TemperatureAnalysis({ data }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground mb-4">
        MAE by forecast horizon — averaged across all runs and stations in the period
      </p>

      <DegradationChart
        degradation={data.degradation}
        color="#5cbdb9"
        unit="°C"
      />

      <div className="grid grid-cols-3 gap-2 mt-4">
        <MetricCard label="Overall MAE"  value={data.mae}  unit="°C" />
        <MetricCard label="RMSE"         value={data.rmse} unit="°C" />
        <MetricCard
          label="Bias"
          value={data.bias !== null ? `${data.bias > 0 ? '+' : ''}${data.bias}` : null}
          unit="°C"
        />
      </div>

      <div className="mt-3 px-3 py-2.5 bg-info/15 rounded-lg">
        <p className="text-xs text-primary">💡 {data.insight}</p>
      </div>
    </div>
  )
}

export default TemperatureAnalysis