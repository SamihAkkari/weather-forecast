// import { MapContainer, TileLayer, CircleMarker, useMapEvents, Tooltip } from 'react-leaflet'

// const FRANCE_CENTER = [46.5, 2.5]
// const DEFAULT_ZOOM = 5


// function ClickHandler({ onLocationClick }) {
//   useMapEvents({
//     click(e) {
//       onLocationClick({ 
//         lat: e.latlng.lat,
//         lng: e.latlng.lng,
//       })
//     }
//   })
//   return null
// }

// function StationMap({ selectedLocation, onLocationClick }) {
//   return (
//     <div className="border border-gray-100 rounded-xl overflow-hidden h-64">
//       <MapContainer
//         center={FRANCE_CENTER}
//         zoom={DEFAULT_ZOOM}
//         style={{ height: '100%', width: '100%' }}
//         zoomControl={false}
//       >
//         <TileLayer
//           url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
//           attribution='© OpenStreetMap contributors'
//         />

//         <ClickHandler onLocationClick={onLocationClick} />

//         {selectedLocation && (
//           <CircleMarker
//             center={[selectedLocation.lat, selectedLocation.lng]}
//             radius={8}
//             pathOptions={{
//               color: '#1d4ed8',
//               fillColor: '#1d4ed8',
//               fillOpacity: 1,
//               weight: 2,
//             }}
//           />
//         )}

//       </MapContainer>
//     </div>
//   )
// }

// export default StationMap



import { useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, useMapEvents, useMap } from 'react-leaflet'

const FRANCE_CENTER = [46.5, 2.5]
const DEFAULT_ZOOM = 5

function ClickHandler({ onLocationClick }) {
  useMapEvents({
    click(e) {
      onLocationClick({ lat: e.latlng.lat, lng: e.latlng.lng })
    }
  })
  return null
}

function FlyToLocation({ location }) {
  const map = useMap()
  if (location) {
    map.flyTo([location.lat, location.lng], 11)
  }
  return null
}


function StationMap({ selectedLocation, onLocationClick }) {
  const [query, setQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState(null)

  function handleSearch(e) {
    e.preventDefault()
    if (!query.trim()) return

    setSearching(true)
    setError(null)

    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1&countrycodes=fr`)
      .then(res => res.json())
      .then(results => {
        if (results.length === 0) {
          setError('Address not found')
          return
        }
        const { lat, lon } = results[0]
        onLocationClick({ lat: parseFloat(lat), lng: parseFloat(lon) })
      })
      .catch(() => setError('Search failed'))
      .finally(() => setSearching(false))
  }

  return (
    <div className="border border-gray-100 rounded-xl overflow-hidden h-64 flex flex-col">

      <form onSubmit={handleSearch} className="flex gap-2 p-2 border-b border-gray-100">
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search an address..."
          className="flex-1 text-sm px-3 py-1.5 rounded-lg border border-gray-100 focus:outline-none focus:border-gray-300"
        />
        <button
          type="submit"
          disabled={searching}
          className="text-sm px-3 py-1.5 rounded-lg border border-gray-100 text-gray-600 hover:border-gray-300 transition-colors disabled:opacity-40"
        >
          {searching ? '...' : 'Go'}
        </button>
      </form>

      {error && (
        <p className="text-xs text-red-400 px-3 py-1">{error}</p>
      )}

      <div className="flex-1">
        <MapContainer
          center={FRANCE_CENTER}
          zoom={DEFAULT_ZOOM}
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='© OpenStreetMap contributors'
          />

          <ClickHandler onLocationClick={onLocationClick} />
          <FlyToLocation location={selectedLocation} />

          {selectedLocation && (
            <CircleMarker
              center={[selectedLocation.lat, selectedLocation.lng]}
              radius={8}
              pathOptions={{
                color: '#1d4ed8',
                fillColor: '#1d4ed8',
                fillOpacity: 1,
                weight: 2,
              }}
            />
          )}

        </MapContainer>
      </div>

    </div>
  )
}

export default StationMap