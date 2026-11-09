/*
  This component receives the daily array from mockWeatherDetails.
  It draws two SVG curves   one for max temps (orange) and one for min temps (blue).

  The key challenge is converting temperatures to Y positions on the SVG canvas.
  We do this with a scale function that maps the temperature range to pixel range.
*/
import { getDailyWeatherIconName, getWeatherIconUrl } from "../../utils/weatherIcons";

/*
  mapValue takes a value in one range and maps it to another range.
  Example: mapValue(15, 0, 30, 10, 130) → maps temp 15 (in range 0-30)
  to a Y pixel value between 10 and 130.

  We use this to convert temperatures to SVG Y coordinates.
  Note: in SVG, Y=0 is at the TOP, so higher temperatures need LOWER Y values.
  That's why we flip the mapping (toMax - result instead of result directly).
*/
function mapValue(value, fromMin, fromMax, toMin, toMax) {
  const ratio = (value - fromMin) / (fromMax - fromMin);
  return toMax - ratio * (toMax - toMin);
}

/*
  buildCurvePath takes an array of {x, y} points and returns a smooth
  SVG cubic bezier path string. The control points are computed automatically
  by offsetting horizontally   this gives the smooth S-curve look without
  needing to calculate full bezier handles manually.
*/
function buildCurvePath(points) {
  if (points.length < 2) return "";
  let d = `M${points[0].x},${points[0].y}`;
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    const cpX = (prev.x + curr.x) / 2;
    d += ` C${cpX},${prev.y} ${cpX},${curr.y} ${curr.x},${curr.y}`;
  }
  return d;
}

function DailyForecast({ daily }) {
  // There is nothing to render before daily forecast data is available.
  if (!daily || daily.length === 0) return null;

  /*
    SVG dimensions and layout constants.
    We define these once here so they're easy to adjust.
    The curve drawing area sits between Y=20 (top) and Y=90 (bottom),
    leaving room above for max temp labels and below for icons and day names.
  */
  const WIDTH = 620;
  const HEIGHT = 150;
  const CURVE_TOP = 25; // highest Y a curve point can reach
  const CURVE_BOT = 88; // lowest Y a curve point can reach
  const LABEL_PAD = 12; // pixels above/below a dot for its label

  /*
    Compute X positions   evenly spaced across the SVG width.
    We add padding on both sides so the first and last points
    don't sit right at the edge.
  */
  const paddingX = 50;
  const step = (WIDTH - paddingX * 2) / (daily.length - 1);
  const xPositions = daily.map((_, i) => paddingX + i * step);

  /*
    Find the global min and max across ALL days.
    This is important   we scale both curves against the same range
    so their relative positions are meaningful.
    For example if min is always close to max the curves would look flat
    without this global scaling.
  */
  const allTemps = daily.flatMap((d) => [d.min, d.max]);
  const globalMin = Math.min(...allTemps);
  const globalMax = Math.max(...allTemps);
  /*
    We add a small padding to the temp range so the curves
    don't touch the very top or bottom of the drawing area.
  */
  const tempPad = 2;
  const scaledMin = globalMin - tempPad;
  const scaledMax = globalMax + tempPad;

  /*
    Build the point arrays for both curves.
    Each point has x (position along SVG) and y (mapped temperature).
  */
  const maxPoints = daily.map((d, i) => ({
    x: xPositions[i],
    y: mapValue(d.max, scaledMin, scaledMax, CURVE_TOP, CURVE_BOT),
  }));

  const minPoints = daily.map((d, i) => ({
    x: xPositions[i],
    y: mapValue(d.min, scaledMin, scaledMax, CURVE_TOP, CURVE_BOT),
  }));

  const maxPath = buildCurvePath(maxPoints);
  const minPath = buildCurvePath(minPoints);

  return (
    <div>
      <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-primary mb-4">
        Daily forecast
      </p>
      <div className="glass border border-border rounded-2xl px-5 py-4 glass">
        <svg width="100%" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} preserveAspectRatio="xMidYMid meet">
          <defs>
            {/* Gradient fills under each curve */}
            <linearGradient id="maxGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f97316" stopOpacity="0.12" />
              <stop offset="100%" stopColor="#f97316" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="minGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#5cbdb9" stopOpacity="0" />
              <stop offset="100%" stopColor="#5cbdb9" stopOpacity="0.10" />
            </linearGradient>
          </defs>

          {/*
            Area fills   we close the path down to the bottom of the SVG
            to create the shaded area under each curve.
          */}
          <path
            d={`${maxPath} L${xPositions[daily.length - 1]},${HEIGHT} L${xPositions[0]},${HEIGHT} Z`}
            fill="url(#maxGrad)"
            stroke="none"
          />
          <path
            d={`${minPath} L${xPositions[daily.length - 1]},${HEIGHT} L${xPositions[0]},${HEIGHT} Z`}
            fill="url(#minGrad)"
            stroke="none"
          />

          {/* The two curves */}
          <path d={maxPath} fill="none" stroke="#f97316" strokeWidth="2" strokeLinecap="round" />
          <path d={minPath} fill="none" stroke="#5cbdb9" strokeWidth="2" strokeLinecap="round" />

          {/* Dots and labels for each day */}
          {daily.map((d, i) => (
            <g key={i}>
              {/* Max temp dot */}
              <circle cx={xPositions[i]} cy={maxPoints[i].y} r="3" fill="#f97316" />
              {/* Max temp label   sits above the dot */}
              <text
                x={xPositions[i]}
                y={maxPoints[i].y - LABEL_PAD}
                textAnchor="middle"
                fontSize="11"
                fill="#f97316"
                fontWeight="500"
              >
                {d.max}°
              </text>

              {/* Min temp dot */}
              <circle cx={xPositions[i]} cy={minPoints[i].y} r="3" fill="#5cbdb9" />
              {/* Min temp label   sits below the dot */}
              <text
                x={xPositions[i]}
                y={minPoints[i].y + LABEL_PAD + 4}
                textAnchor="middle"
                fontSize="11"
                fill="#5cbdb9"
                fontWeight="500"
              >
                {d.min}°
              </text>

              {/* Weather icon */}
              {/* <text
                x={xPositions[i]}
                y={HEIGHT - 18}
                textAnchor="middle"
                fontSize="14"
              >
                {ICONS[d.icon] ?? '🌤'}
              </text> */}

              {/* Weather icon */}
              <image
                href={getWeatherIconUrl(getDailyWeatherIconName(d.weather_code))}
                x={xPositions[i] - 16}
                y={HEIGHT - 48}
                width="32"
                height="32"
                role="img"
                aria-label={`Weather code ${d.weather_code}`}
                preserveAspectRatio="xMidYMid meet"
              />

              {/* Day name */}
              <text
                x={xPositions[i]}
                y={HEIGHT - 4}
                textAnchor="middle"
                fontSize="10"
                fill="#8fb3c4"
              >
                {d.day}
              </text>
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
}

export default DailyForecast;
