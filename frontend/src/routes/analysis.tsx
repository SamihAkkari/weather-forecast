import { lazy } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ClientPage } from "../app/ClientPage";

const Page = lazy(() => import("../app/pages/AnalysisPage"));

export const Route = createFileRoute("/analysis")({
  head: () => ({
    meta: [
      { title: "Analysis tool — MeteoApp" },
      { name: "description", content: "Compare stations, explore historical weather data and export CSV files." },
      { property: "og:title", content: "Analysis tool — MeteoApp" },
      { property: "og:description", content: "Historical weather analysis and CSV export." },
    ],
  }),
  component: () => <ClientPage Page={Page} />,
});
