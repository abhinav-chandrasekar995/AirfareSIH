"use client";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { FilterBar } from "@/components/filters/FilterBar";
import { QualityIndicator } from "@/components/badges/QualityIndicator";
import { EmptyState, ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { useAirlines, useFares, useRoutes } from "@/lib/api/hooks";
import { inr, istDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import { Download } from "lucide-react";

const LEAD_BUCKETS = ["T1", "T7", "T15", "T30", "T45"];

export default function DataExplorerPageInner() {
  const search = useSearchParams();
  const [route, setRoute] = useState(search.get("route") ?? "");
  const [airline, setAirline] = useState(search.get("airline") ?? "");
  const [leadBucket, setLeadBucket] = useState("");
  const [qualityMin, setQualityMin] = useState(60);
  const [page, setPage] = useState(1);

  const { data: routes } = useRoutes();
  const { data: airlines } = useAirlines();
  const { data, isLoading, isError, error } = useFares({
    route: route || undefined, airline: airline || undefined, lead_bucket: leadBucket || undefined,
    quality_min: qualityMin, page, page_size: 50,
  });

  const exportUrl = `/backend/api/v1/fares/export?fmt=csv${route ? `&route=${route}` : ""}${airline ? `&airline=${airline}` : ""}&quality_min=${qualityMin}`;

  return (
    <div>
      <PageHeader
        title="Data Explorer"
        subtitle="Inspect individual fare observations — full transparency into the analytical pipeline"
        actions={
          <a href={exportUrl} className="inline-flex items-center gap-1.5 text-xs bg-interactive text-white px-3 py-1.5 rounded-md hover:bg-interactive-hover">
            <Download size={13} /> Export CSV
          </a>
        }
      />

      <FilterBar className="mb-3">
        <select value={route} onChange={(e) => { setRoute(e.target.value); setPage(1); }} className="text-xs bg-panel border border-border-subtle rounded-md px-2 py-1.5">
          <option value="">All routes</option>
          {routes?.data.map((r) => <option key={r.route_code} value={r.route_code}>{r.route_code}</option>)}
        </select>
        <select value={airline} onChange={(e) => { setAirline(e.target.value); setPage(1); }} className="text-xs bg-panel border border-border-subtle rounded-md px-2 py-1.5">
          <option value="">All airlines</option>
          {airlines?.data.map((a) => <option key={a.airline_code} value={a.airline_code}>{a.name}</option>)}
        </select>
        <select value={leadBucket} onChange={(e) => { setLeadBucket(e.target.value); setPage(1); }} className="text-xs bg-panel border border-border-subtle rounded-md px-2 py-1.5">
          <option value="">All lead windows</option>
          {LEAD_BUCKETS.map((b) => <option key={b} value={b}>T+{b.replace("T", "")}</option>)}
        </select>
        <label className="flex items-center gap-1.5 text-xs text-secondary">
          Quality ≥
          <input type="number" min={0} max={100} value={qualityMin} onChange={(e) => setQualityMin(Number(e.target.value))} className="w-14 bg-panel border border-border-subtle rounded-md px-1.5 py-1" />
        </label>
      </FilterBar>

      <PanelShell title="Fare Observations" source="fare_observations" count={data?.meta.total ?? data?.data.length} qualityThreshold={qualityMin}>
        {isLoading ? (
          <Skeleton className="h-96" />
        ) : isError ? (
          <ErrorState message={error instanceof Error ? error.message : "Could not load observations."} />
        ) : !data || data.data.length === 0 ? (
          <EmptyState title="No observations match these filters" message="Try widening the route, lead-time or quality filter." />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead>
                  <tr className="border-b border-border-strong text-left sticky top-0 bg-panel">
                    <th className="eyebrow font-semibold py-1.5 pr-2">Observed</th>
                    <th className="eyebrow font-semibold py-1.5 pr-2">Route</th>
                    <th className="eyebrow font-semibold py-1.5 pr-2">Airline</th>
                    <th className="eyebrow font-semibold py-1.5 pr-2">Flight</th>
                    <th className="eyebrow font-semibold py-1.5 pr-2">Lead</th>
                    <th className="eyebrow font-semibold py-1.5 pr-2 text-right">Base</th>
                    <th className="eyebrow font-semibold py-1.5 pr-2 text-right">Tax</th>
                    <th className="eyebrow font-semibold py-1.5 pr-2 text-right">Total</th>
                    <th className="eyebrow font-semibold py-1.5 pr-2">Source</th>
                    <th className="eyebrow font-semibold py-1.5">Quality</th>
                  </tr>
                </thead>
                <tbody>
                  {data.data.map((o) => (
                    <tr key={o.observation_id} className={cn("border-b border-border-subtle numeric", o.is_outlier && "bg-[var(--warn-100)]/40")}>
                      <td className="py-1.5 pr-2 text-muted">{istDateTime(o.observed_at)}</td>
                      <td className="py-1.5 pr-2 mono font-medium">{o.route_code}</td>
                      <td className="py-1.5 pr-2">{o.airline_code}</td>
                      <td className="py-1.5 pr-2 mono">{o.flight_number}</td>
                      <td className="py-1.5 pr-2">T+{o.lead_days}</td>
                      <td className="py-1.5 pr-2 text-right">{inr(o.base_fare)}</td>
                      <td className="py-1.5 pr-2 text-right">{inr(o.taxes)}</td>
                      <td className="py-1.5 pr-2 text-right font-medium">{inr(o.total_fare)}</td>
                      <td className="py-1.5 pr-2 text-muted">{o.source}</td>
                      <td className="py-1.5"><QualityIndicator score={o.quality_score} band={o.quality_band} showBar={false} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-between mt-3 text-xs text-muted">
              <span>Page {data.meta.page} of {Math.max(1, Math.ceil((data.meta.total ?? 0) / (data.meta.page_size || 50)))}</span>
              <div className="flex gap-2">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="px-2 py-1 rounded-md border border-border-subtle disabled:opacity-40">Prev</button>
                <button onClick={() => setPage((p) => p + 1)} disabled={data.data.length < 50} className="px-2 py-1 rounded-md border border-border-subtle disabled:opacity-40">Next</button>
              </div>
            </div>
          </>
        )}
      </PanelShell>
    </div>
  );
}
