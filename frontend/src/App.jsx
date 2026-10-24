import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import WeatherViewerPage from './pages/WeatherViewerPage'
import AnalysisPage from './pages/AnalysisPage'
import ActivityPage from './pages/ActivityPage'
import WidgetDetailPage from './pages/WidgetDetailPage'
import PvProductionPage from './pages/PvProductionPage'

function App() {
  const [selectedLocation, setSelectedLocation] = useState(null)

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/viewer"
          element={
            <WeatherViewerPage
              selectedLocation={selectedLocation}
              onLocationChange={setSelectedLocation}
            />
          }
        />
        <Route path="/analysis" element={<AnalysisPage />} />
        <Route path="/activity/:id" element={<ActivityPage />} />
        <Route path="/widget/:id" element={<WidgetDetailPage />} />
        <Route
          path="/pv"
          element={
            <PvProductionPage
              selectedLocation={selectedLocation}
            />
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App