/*
  This file contains one utility function that converts analysis data
  to a CSV file and triggers a browser download.

  We put it in src/utils/ because it is pure logic with no React in it —
  it does not render anything, it does not use hooks, it just takes data
  and produces a side effect (a file download). This separation makes it
  easy to test and reuse.
*/

/*
  arrayToCsv takes an array of objects and converts it to a CSV string.

  Example input:
  [
    { time: "2026-04-21T00:00:00", forecast: 10.2, observed: 9.8 },
    { time: "2026-04-21T01:00:00", forecast: 9.8,  observed: 9.2 },
  ]

  Example output:
  "time,forecast,observed\n2026-04-21T00:00:00,10.2,9.8\n2026-04-21T01:00:00,9.8,9.2"

  Object.keys(rows[0]) extracts the column names from the first object.
  .map(row => Object.values(row).join(',')) converts each object to a CSV line.
  .join('\n') joins all lines with a newline character.
*/
function arrayToCsv(rows) {
  if (!rows || rows.length === 0) return ''
  const headers = Object.keys(rows[0]).join(',')
  const lines = rows.map(row => Object.values(row).join(','))
  return [headers, ...lines].join('\n')
}

/*
  downloadCsv triggers a file download in the browser.

  It works by:
  1. Creating a Blob (a raw binary object) from the CSV string
  2. Creating a temporary invisible <a> tag pointing to that blob
  3. Programmatically clicking it to trigger the download
  4. Immediately removing the temporary tag

  This is the standard browser pattern for triggering downloads
  from data that exists in memory — no server needed.
*/
function downloadCsv(content, filename) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/*
  exportAnalysisCsv is the main function called from the page.
  It receives the full analysisData object and exports three CSV files:
  one for temperature comparison, one for rain, one for sunshine.

  We export three separate files rather than one combined file because
  each section has a different shape — mixing them in one file would
  produce an awkward structure that is hard to work with in Excel or Python.

  stationName and runTime are included in the filename so the user
  knows exactly which analysis the file corresponds to.
*/
export function exportAnalysisCsv(analysisData, label) {
  const station = analysisData.station_name?.replace(/\s+/g, '_') ?? 'station'

  // Temperature degradation
  const tempRows = Object.entries(analysisData.temperature.degradation)
    .map(([horizon, mae]) => ({ horizon_h: horizon, mae }))
    .sort((a, b) => a.horizon_h - b.horizon_h)
  downloadCsv(arrayToCsv(tempRows), `temperature_degradation_${station}_${label}.csv`)

  // Rain
  const rainRows = [{ metric: 'rain', ...analysisData.rain }]
  downloadCsv(arrayToCsv(rainRows), `rain_${station}_${label}.csv`)

  // Sunshine
  const sunshineRows = [{ metric: 'sunshine', ...analysisData.sunshine }]
  downloadCsv(arrayToCsv(sunshineRows), `sunshine_${station}_${label}.csv`)
}