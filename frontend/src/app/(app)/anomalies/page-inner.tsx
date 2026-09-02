"use client";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { FilterBar } from "@/components/filters/FilterBar";
import { SeverityBadge } from "@/components/badges/SeverityBadge";
import { EmptyState, ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { useAnomalies } from "@/lib/api/hooks";
import { pct, relativeTime } from "@/lib/format";
import { cn } from "@/lib/utils";

const SEV_BORDER: Record<string, string> = {
  CRITICAL: "border-l-sev-critical", HIGH: "border-l-sev-high",
  MEDIUM: "border-l-sev-medium", LOW: "border-l-sev-low",
};

export default function AnomaliesPageInner() {
  const search = useSearchParams();
  const [severity, setSeverity] = useState("");
  const [route] = useState(search.get("route") ?? "");
  const [anomalyClass, setAnomalyClass] = useState<"MARKET" | "SCRAPER">("MARKET");

  const { data, isLoading, isError, error } = useAnomalies({
    severity: severity || undefined, route: route || undefined, anomaly_class: anomalyClass,
  });

  return (
    <div>
      <PageHeader title="Anomaly & Surge Intelligence" subtitle="Expected fare vs observed fare, with model-based factor attribution" />

      <FilterBar className="mb-3">
        <div className="flex rounded-md border border-border-subtle overflow-hidden text-xs">
          <button onClick={() => setAnomalyClass("MARKET")} className={cn("px-3 py-1.5", anomalyClass === "MARKET" ? "bg-interactive text-white" : "bg-panel text-secondary")}>Market anomalies</button>
          <button onClick={() => setAnomalyClass("SCRAPER")} className={cn("px-3 py-1.5", anomalyClass === "SCRAPER" ? "bg-interactive text-white" : "bg-panel text-secondary")}>Data-quality flags</button>
        </div>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="text-xs bg-panel border border-border-subtle rounded-md px-2 py-1.5">
          <option value="">All severities</option>
          {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </FilterBar>

      <PanelShell title={anomalyClass === "MARKET" ? "Market Anomalies" : "Data-Quality Flags"} source="anomalies" count={data?.data.length}>
        {isLoading ? (
          <Skeleton className="h-96" />
        ) : isError ? (
          <ErrorState message={error instanceof Error ? error.message : "Could not load anomalies."} />
        ) : !data || data.data.length === 0 ? (
          <EmptyState title="No anomalies found" message="No anomalies match the current filters." />
        ) : (
          <ul className="divide-y divide-border-subtle">
            {data.data.map((a) => (
              <li key={a.anomaly_id}>
                <Link
                  href={`/anomalies/${a.anomaly_id}`}
                  className={cn("flex items-center justify-between gap-3 py-2.5 px-2 -mx-2 border-l-2 hover:bg-panel-alt/50", SEV_BORDER[a.severity])}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <SeverityBadge severity={a.severity} />
                    <div className="min-w-0">
                      <div className="text-xs font-medium text-primary mono">{a.route_code}</div>
                      <div className="text-[11px] text-muted truncate">{a.origin_city} → {a.destination_city}</div>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className={cn("text-xs font-semibold numeric", a.deviation_pct > 0 ? "text-price-up" : "text-price-down")}>{pct(a.deviation_pct)}</div>
                    <div className="text-[11px] text-muted">{relativeTime(a.detected_at)}</div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </PanelShell>
    </div>
  );
}
