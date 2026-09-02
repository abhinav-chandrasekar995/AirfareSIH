"use client";
import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { FilterBar } from "@/components/filters/FilterBar";
import { QualityIndicator } from "@/components/badges/QualityIndicator";
import { EmptyState, ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { useRoutes } from "@/lib/api/hooks";
import { inr, num, pct } from "@/lib/format";
import { cn } from "@/lib/utils";

const VOL_COLOR: Record<string, string> = { HIGH: "text-sev-high", MEDIUM: "text-sev-medium", LOW: "text-sev-low" };

export default function RoutesPage() {
  const { data, isLoading, isError, error } = useRoutes();
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");

  const airports = useMemo(() => {
    if (!data) return { origins: [], destinations: [] };
    const origins = Array.from(new Set(data.data.map((r) => r.origin))).sort();
    const destinations = Array.from(new Set(data.data.map((r) => r.destination))).sort();
    return { origins, destinations };
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.data.filter(
      (r) => (!origin || r.origin === origin) && (!destination || r.destination === destination),
    );
  }, [data, origin, destination]);

  // When the A -> B filter narrows to exactly one route, show a compact stats summary
  // above the table - reusing fields already present in the fetched RouteSummary, so
  // no extra network round trip is needed to answer "show the stats" for that pair.
  const single = origin && destination && filtered.length === 1 ? filtered[0] : null;

  return (
    <div>
      <PageHeader title="Route Intelligence" subtitle="Every tracked city-pair, with fare, index and volatility" />

      <FilterBar className="mb-3">
        <select value={origin} onChange={(e) => setOrigin(e.target.value)} className="text-xs bg-panel border border-border-subtle rounded-md px-2 py-1.5" aria-label="Origin airport">
          <option value="">Origin (any)</option>
          {airports.origins.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        <ArrowRight size={13} className="text-muted" />
        <select value={destination} onChange={(e) => setDestination(e.target.value)} className="text-xs bg-panel border border-border-subtle rounded-md px-2 py-1.5" aria-label="Destination airport">
          <option value="">Destination (any)</option>
          {airports.destinations.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
        {(origin || destination) && (
          <button onClick={() => { setOrigin(""); setDestination(""); }} className="text-xs text-muted hover:text-primary underline">
            Reset
          </button>
        )}
      </FilterBar>

      {single && (
        <PanelShell
          title={`${single.origin} → ${single.destination} — Route Stats`}
          subtitle={`${single.origin_city} to ${single.destination_city}`}
          source="routes, index_values"
          className="mb-4"
        >
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <div className="eyebrow">Current Fare</div>
              <div className="text-xl font-extrabold numeric mt-1">{inr(single.current_fare)}</div>
            </div>
            <div>
              <div className="eyebrow">Route Index</div>
              <div className="text-xl font-extrabold numeric mt-1">{num(single.route_index, 1)}</div>
            </div>
            <div>
              <div className="eyebrow">Basket Weight</div>
              <div className="text-xl font-extrabold numeric mt-1">{single.weight ? pct(single.weight * 100, 1, false) : "—"}</div>
            </div>
            <div>
              <div className="eyebrow">Volatility</div>
              <div className={cn("text-xl font-extrabold mt-1", single.volatility_score && VOL_COLOR[single.volatility_score])}>
                {single.volatility_score ?? "—"}
              </div>
            </div>
          </div>
          <div className="flex gap-4 mt-4 pt-3 border-t-[var(--border-hard)] border-border-strong">
            <Link href={`/routes/${single.route_code}`} className="text-xs text-accent hover:underline">Full route detail →</Link>
            <Link href={`/lead-time?route=${single.route_code}`} className="text-xs text-accent hover:underline">Lead-time curve →</Link>
            <Link href={`/anomalies?route=${single.route_code}`} className="text-xs text-accent hover:underline">Anomalies →</Link>
          </div>
        </PanelShell>
      )}

      <PanelShell title="Tracked Routes" source="routes, index_values" count={filtered.length}>
        {isLoading ? (
          <Skeleton className="h-96" />
        ) : isError ? (
          <ErrorState message={error instanceof Error ? error.message : "Could not load routes."} />
        ) : !data || data.data.length === 0 ? (
          <EmptyState title="No routes yet" message="No routes are in the active basket." />
        ) : filtered.length === 0 ? (
          <EmptyState title="No route matches this pair" message={`No tracked route runs from ${origin || "any origin"} to ${destination || "any destination"}.`} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border-strong text-left">
                  <th className="eyebrow font-semibold py-1.5">Route</th>
                  <th className="eyebrow font-semibold py-1.5">Region</th>
                  <th className="eyebrow font-semibold py-1.5 text-right">Current Fare</th>
                  <th className="eyebrow font-semibold py-1.5 text-right">Route Index</th>
                  <th className="eyebrow font-semibold py-1.5 text-right">Weight</th>
                  <th className="eyebrow font-semibold py-1.5">Volatility</th>
                  <th className="eyebrow font-semibold py-1.5 text-right">n</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.route_code} className="border-b border-border-subtle hover:bg-panel-alt/50">
                    <td className="py-2">
                      <Link href={`/routes/${r.route_code}`} className="font-medium text-primary hover:text-accent mono">{r.route_code}</Link>
                      <div className="text-[11px] text-muted">{r.origin_city} → {r.destination_city}</div>
                    </td>
                    <td className="py-2 text-secondary">{r.region}</td>
                    <td className="py-2 text-right numeric">{inr(r.current_fare)}</td>
                    <td className="py-2 text-right numeric font-medium">{num(r.route_index, 1)}</td>
                    <td className="py-2 text-right numeric text-muted">{r.weight ? `${(r.weight * 100).toFixed(1)}%` : "—"}</td>
                    <td className={cn("py-2 font-medium", r.volatility_score && VOL_COLOR[r.volatility_score])}>{r.volatility_score ?? "—"}</td>
                    <td className="py-2 text-right numeric text-muted">{r.n_observations}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </PanelShell>
    </div>
  );
}
