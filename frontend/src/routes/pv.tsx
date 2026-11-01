import { lazy } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ClientPage } from "../app/ClientPage";
import { useSelectedLocation } from "../app/LocationContext";

const Page = lazy(() => import("../app/pages/PvProductionPage"));

export const Route = createFileRoute("/pv")({
  head: () => ({
    meta: [
      { title: "PV production — MeteoApp" },
      { name: "description", content: "Estimate solar panel production from the local forecast." },
      { property: "og:title", content: "PV production — MeteoApp" },
      { property: "og:description", content: "Solar production estimates from weather forecasts." },
    ],
  }),
  component: Pv,
});

function Pv() {
  const { selectedLocation } = useSelectedLocation();
  return <ClientPage Page={Page} props={{ selectedLocation }} />;
}
