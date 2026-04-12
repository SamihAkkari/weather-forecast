import { MapContainer, TileLayer, CircleMarker, useMapEvents, Tooltip } from 'react-leaflet'

const FRANCE_CENTER = [46.5, 2.5]
const DEFAULT_ZOOM = 5


function ClickHandler({ onLocationClick }) {
  useMapEvents({
    click(e) {
      onLocationClick({ 
        lat: e.latlng.lat,
        lng: e.latlng.lng,
      })
    }
  })
  return null
}

function StationMap({ selectedLocation, onLocationClick }) {
  return (
    <div className="border border-gray-100 rounded-xl overflow-hidden h-64">
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
  )
}

export default StationMap



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

//         {stations.map(station => {
//           const isSelected = selectedStation?.id === station.id
//           return (
//             <CircleMarker
//               key={station.id}
//               center={[station.latitude, station.longitude]}
//               radius={isSelected ? 8 : 5}
//               pathOptions={{
//                 color: isSelected ? '#1d4ed8' : '#378ADD',
//                 fillColor: isSelected ? '#1d4ed8' : '#378ADD',
//                 fillOpacity: isSelected ? 1 : 0.6,
//                 weight: isSelected ? 2 : 1,
//               }}
//               eventHandlers={{
//                 click: () => onStationClick(station)
//               }}
//             >
//               <Tooltip direction="top" offset={[0, -8]}>
//                 <div>
//                   <div>{station.name}</div>
//                   <div>{station.altitude} m</div>
//                 </div>
//               </Tooltip>
//             </CircleMarker>
//           )
//         })}
//       </MapContainer>
//     </div>
//   )
// }

// export default StationMap