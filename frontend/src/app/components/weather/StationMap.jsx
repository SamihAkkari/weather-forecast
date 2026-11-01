import { useEffect, useRef, useState } from "react";
import {
  CircleMarker,
  MapContainer,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";

const FRANCE_CENTER = [46.5, 2.5];
const DEFAULT_ZOOM = 5;

function ClickHandler({ onLocationClick }) {
  useMapEvents({
    click(e) {
      onLocationClick({ lat: e.latlng.lat, lng: e.latlng.lng });
    },
  });
  return null;
}

function FlyToLocation({ location }) {
  const map = useMap();
  if (location) {
    map.flyTo([location.lat, location.lng], 11);
  }
  return null;
}

function StationMap({ selectedLocation, onLocationClick }) {
  const [query, setQuery] = useState("");
  const [error, setError] = useState(null);
  const [searching, setSearching] = useState(false);
  const searchController = useRef(null);

  useEffect(() => {
    return () => searchController.current?.abort();
  }, []);

  async function handleSearch(e) {
    e.preventDefault();
    const address = query.trim();
    if (!address || searching) {
      return;
    }

    setSearching(true);
    setError(null);
    searchController.current?.abort();
    const controller = new AbortController();
    searchController.current = controller;

    try {
      const params = new URLSearchParams({
        format: "jsonv2",
        q: address,
        limit: "1",
        countrycodes: "fr",
      });
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?${params}`,
        { signal: controller.signal },
      );
      if (!response.ok) {
        throw new Error(`Address search failed (${response.status}).`);
      }

      const results = await response.json();
      if (results.length === 0) {
        setError("Address not found. Try a more specific search.");
        return;
      }

      const { lat, lon } = results[0];
      onLocationClick({ lat: Number(lat), lng: Number(lon) });
    } catch (searchError) {
      if (searchError.name !== "AbortError") {
        console.error("Address search failed.", searchError);
        setError("Address search failed. Please try again.");
      }
    } finally {
      if (!controller.signal.aborted) {
        setSearching(false);
      }
    }
  }

  return (
    <div className="glass border border-border rounded-2xl overflow-hidden h-[440px] flex flex-col shadow-[var(--shadow-glow)]">
      <form onSubmit={handleSearch} className="flex gap-2 p-2 border-b border-border">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search an address..."
          aria-label="Search an address in France"
          className="flex-1 text-sm px-3 py-1.5 rounded-lg border border-border focus:outline-none focus:border-primary/40"
        />
        <button
          type="submit"
          disabled={searching || !query.trim()}
          className="text-sm px-3 py-1.5 rounded-lg border border-border text-muted-foreground lift transition-colors"
        >
          {searching ? "Searching..." : "Go"}
        </button>
      </form>

      {error && (
        <p role="alert" className="text-xs text-destructive px-3 py-1">
          {error}
        </p>
      )}

      <div className="flex-1">
        <MapContainer
          center={FRANCE_CENTER}
          zoom={DEFAULT_ZOOM}
          style={{ height: "100%", width: "100%" }}
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
          />
          <ClickHandler onLocationClick={onLocationClick} />
          <FlyToLocation location={selectedLocation} />

          {selectedLocation && (
            <CircleMarker
              center={[selectedLocation.lat, selectedLocation.lng]}
              radius={8}
              pathOptions={{
                color: "#5cbdb9",
                fillColor: "#5cbdb9",
                fillOpacity: 1,
                weight: 2,
              }}
            />
          )}
        </MapContainer>
      </div>
    </div>
  );
}

export default StationMap;
