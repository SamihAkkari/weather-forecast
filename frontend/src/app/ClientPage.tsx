import { Suspense, type ComponentType } from "react";
import { ClientOnly } from "@tanstack/react-router";

// Map/chart pages touch `window` on import, so render them only in the browser.
export function ClientPage<P extends object>({
  Page,
  props,
}: {
  Page: ComponentType<P>;
  props: P;
}) {
  const fallback = <div className="min-h-screen bg-background" />;
  return (
    <ClientOnly fallback={fallback}>
      <Suspense fallback={fallback}>
        <Page {...props} />
      </Suspense>
    </ClientOnly>
  );
}
