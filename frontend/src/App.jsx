import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import WeatherViewerPage from './pages/WeatherViewerPage'
import AnalysisPage from './pages/AnalysisPage'


function App() {
  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route index element={<HomePage />} />
          <Route path="/viewer" element={<WeatherViewerPage />} />
          <Route path="/analysis" element={<AnalysisPage />} />

        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App
