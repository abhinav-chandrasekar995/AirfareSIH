import { Suspense } from "react";
import AnomaliesPageInner from "./page-inner";

// useSearchParams() requires a Suspense boundary at build time (Next.js 14 static
// export requirement) - split into a thin server wrapper + the client page.
export default function AnomaliesPage() {
  return (
    <Suspense fallback={null}>
      <AnomaliesPageInner />
    </Suspense>
  );
}
