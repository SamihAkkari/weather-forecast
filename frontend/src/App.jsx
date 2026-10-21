import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import WeatherViewerPage from './pages/WeatherViewerPage'
import AnalysisPage from './pages/AnalysisPage'
import ActivityPage from './pages/ActivityPage'

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
      </Routes>
    </BrowserRouter>
  )
}

export default App