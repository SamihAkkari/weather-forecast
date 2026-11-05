import { lazy } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ClientPage } from "../app/ClientPage";

const Page = lazy(() => import("../app/pages/ActivityPage"));

export const Route = createFileRoute("/activity/$id")({
  head: () => ({
    meta: [
      { title: "Activity forecast   MeteoApp" },
      { name: "description", content: "Best time windows for your outdoor activity." },
      { property: "og:title", content: "Activity forecast   MeteoApp" },
      { property: "og:description", content: "Best time windows for your outdoor activity." },
    ],
  }),
  component: () => <ClientPage Page={Page} />,
});
