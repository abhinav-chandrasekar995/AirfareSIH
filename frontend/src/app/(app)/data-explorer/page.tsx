import { Suspense } from "react";
import DataExplorerPageInner from "./page-inner";

export default function DataExplorerPage() {
  return (
    <Suspense fallback={null}>
      <DataExplorerPageInner />
    </Suspense>
  );
}
