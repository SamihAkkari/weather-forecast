import { lazy } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ClientPage } from "../app/ClientPage";

const Page = lazy(() => import("../app/pages/WidgetDetailPage"));

export const Route = createFileRoute("/widget/$id")({
  head: () => ({
    meta: [
      { title: "Weather detail   MeteoApp" },
      { name: "description", content: "Detailed view of a weather measurement." },
      { property: "og:title", content: "Weather detail   MeteoApp" },
      { property: "og:description", content: "Detailed view of a weather measurement." },
    ],
  }),
  component: () => <ClientPage Page={Page} />,
});
