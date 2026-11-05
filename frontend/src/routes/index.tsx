import { createFileRoute } from "@tanstack/react-router";
import HomePage from "../app/pages/HomePage";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "MeteoApp   French weather, from the source" },
      { name: "description", content: "Real Météo-France observations and AROME forecasts, analysis and PV production estimates." },
      { property: "og:title", content: "MeteoApp   French weather, from the source" },
      { property: "og:description", content: "Real Météo-France observations and AROME forecasts." },
    ],
  }),
  component: HomePage,
});
