import { lazy } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ClientPage } from "../app/ClientPage";
import { useSelectedLocation } from "../app/LocationContext";

const Page = lazy(() => import("../app/pages/WeatherViewerPage"));

export const Route = createFileRoute("/viewer")({
  head: () => ({
    meta: [
      { title: "Weather viewer — MeteoApp" },
      { name: "description", content: "Pick a station on the map and see current conditions and the forecast." },
      { property: "og:title", content: "Weather viewer — MeteoApp" },
      { property: "og:description", content: "Station conditions and forecasts across France." },
    ],
  }),
  component: Viewer,
});

function Viewer() {
  const { selectedLocation, setSelectedLocation } = useSelectedLocation();
  return <ClientPage Page={Page} props={{ selectedLocation, onLocationChange: setSelectedLocation }} />;
}
