/*
  This component is used for both rain and sunshine detection.
  It receives a title and a data object shaped like:
  { tp, fp, fn, tn, precision, recall, f1, insight }

  We made it generic on purpose — rain and sunshine have exactly
  the same structure, so building one component and reusing it twice
  is cleaner than building two nearly identical components.
  This is one of the most important principles in React: if two things
  look the same, make one component and pass the differences as props.
*/

/*
  ConfusionMatrix is an internal component that renders the 2x2 grid.
  It receives the four values: tp, fp, fn, tn.

  The confusion matrix is a standard tool in binary classification evaluation.
  Each cell tells a different story:
  - True Positive (tp):  model said YES, reality was YES → correct
  - False Positive (fp): model said YES, reality was NO  → false alarm
  - False Negative (fn): model said NO,  reality was YES → missed event
  - True Negative (tn):  model said NO,  reality was NO  → correct
*/
function ConfusionMatrix({ tp, fp, fn, tn }) {
  return (
    <div>
      {/*
        Column headers explain what the model predicted.
        Row context (actual) is implicit from position.
      */}
      <div className="grid grid-cols-2 gap-1 mb-1">
        <p className="text-xs text-gray-300 text-center">Predicted yes</p>
        <p className="text-xs text-gray-300 text-center">Predicted no</p>
      </div>

      <div className="grid grid-cols-2 gap-1">
        {/*
          Blue cells = correct predictions (model was right)
          Red cells  = incorrect predictions (model was wrong)
        */}
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

/*
  MetricBar renders a single metric as a label, a progress bar, and a percentage.
  The progress bar gives an immediate visual sense of the score
  without the user having to interpret a raw number.

  percent is a value between 0 and 1 (e.g. 0.73 for 73%).
  We multiply by 100 for display and for the bar width.
*/
function MetricBar({ label, percent }) {
  const display = Math.round(percent * 100)

  /*
    Bar color changes based on performance:
    - green  if score >= 80%  → good
    - yellow if score >= 60%  → acceptable
    - red    if score < 60%   → poor
    This gives the user an instant visual signal without needing to read the number.
  */
  const barColor =
    display >= 80 ? 'bg-green-400' :
    display >= 60 ? 'bg-yellow-400' :
    'bg-red-400'

  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-xs font-medium text-gray-700">{display}%</p>
      </div>
      {/*
        The outer div is the grey track.
        The inner div is the filled bar — its width is set inline because
        Tailwind cannot generate dynamic widths from runtime values.
        This is one of the few cases where inline styles are the right choice.
      */}
      <div className="w-full bg-gray-100 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full ${barColor}`}
          style={{ width: `${display}%` }}
        />
      </div>
    </div>
  )
}

function DetectionAnalysis({ title, data }) {
  return (
    <div className="border border-gray-100 rounded-xl p-5">

      <p className="text-xs text-gray-400 mb-4">{title}</p>

      {/*
        Two column layout: confusion matrix on the left, metrics on the right.
        This keeps the component compact so both rain and sunshine
        can sit side by side on the page without taking too much vertical space.
      */}
      <div className="grid grid-cols-2 gap-6">

        <ConfusionMatrix
          tp={data.tp}
          fp={data.fp}
          fn={data.fn}
          tn={data.tn}
        />

        {/*
          Metrics column.
          We use MetricBar for all three so the user can compare
          precision, recall and F1 at a glance visually.
        */}
        <div className="flex flex-col justify-center gap-4">
          <MetricBar label="Precision" percent={data.precision} />
          <MetricBar label="Recall" percent={data.recall} />
          <MetricBar label="F1 score" percent={data.f1} />
        </div>

      </div>

      {/* Insight sentence below the two columns */}
      <div className="mt-4 px-3 py-2.5 bg-blue-50 rounded-lg">
        <p className="text-xs text-blue-700">💡 {data.insight}</p>
      </div>

    </div>
  )
}

export default DetectionAnalysis