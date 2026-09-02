import { Suspense } from "react";
import LeadTimePageInner from "./page-inner";

export default function LeadTimePage() {
  return (
    <Suspense fallback={null}>
      <LeadTimePageInner />
    </Suspense>
  );
}
