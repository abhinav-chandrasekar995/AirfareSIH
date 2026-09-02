"use client";
import { useMemo, useState } from "react";
import Link from "next/link";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { EmptyState, ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { AirfareGlobe } from "@/components/charts/AirfareGlobe";
import { useDashboard } from "@/lib/api/hooks";
import { num } from "@/lib/format";
import { cn } from "@/lib/utils";

const PRESSURE_DOT: Record<string, string> = {
  HIGH: "bg-[var(--down-600)]",
  MEDIUM: "bg-[var(--warn-600)]",
  LOW: "bg-[var(--up-600)]",
};

// The "zoomed in" destination the dashboard's Airfare Pressure Map card links to: the
// same India-focused 3D globe, large and fully draggable, as the single interactive
// element on the page (no separate flat map alongside it). The route table below is a
// plain lookup/search, not a second way to explore the same globe interaction.
export default function PressureMapPage() {
  const { data, isLoading, isError, error } = useDashboard();
  const [query, setQuery] = useState("");

  const points = data?.data.pressure_map ?? [];
  const filtered = useMemo(() => {
    if (!query) return points;
    const q = query.trim().toUpperCase();
    return points.filter(
      (p) =>
        p.route_code.includes(q) ||
        p.origin_city.toUpperCase().includes(q) ||
        p.destination_city.toUpperCase().includes(q),
    );
  }, [points, query]);

  return (
    <div>
      <Breadcrumbs items={[{ label: "Home", href: "/dashboard" }, { label: "Airfare Pressure Map" }]} />
      <PageHeader
        title="Airfare Pressure Map"
        subtitle="Every tracked route plotted as an airway line on a globe facing India, coloured by price pressure vs the index base — drag to rotate, scroll to zoom"
      />

      {isLoading ? (
        <Skeleton className="h-96" />
      ) : isError || !data ? (
        <ErrorState message={error instanceof Error ? error.message : "The pressure map could not be loaded."} />
      ) : points.length === 0 ? (
        <EmptyState title="No pressure data yet" message="The index has not been computed for any route." />
      ) : (
        <>
          <div className="mb-4">
            <PanelShell
              title="Globe"
              subtitle="Facing India — drag to rotate, scroll to zoom in on the route lines"
              source="index_values, routes"
              count={points.length}
            >
              <AirfareGlobe points={points} expanded className="max-w-xl mx-auto" />
              <div className="flex items-center justify-center gap-4 mt-3 text-[11px] text-muted">
                <span className="flex items-center gap-1"><span className={cn("h-2 w-2 rounded-full inline-block", PRESSURE_DOT.LOW)} /> Low</span>
                <span className="flex items-center gap-1"><span className={cn("h-2 w-2 rounded-full inline-block", PRESSURE_DOT.MEDIUM)} /> Medium</span>
                <span className="flex items-center gap-1"><span className={cn("h-2 w-2 rounded-full inline-block", PRESSURE_DOT.HIGH)} /> High</span>
              </div>
            </PanelShell>
          </div>

          <PanelShell title="All Tracked Routes" subtitle="Search, then open a route for the full detail page" source="index_values, routes" count={filtered.length}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by route code or city…"
              className="w-full sm:w-72 text-xs bg-panel border border-border-subtle rounded-md px-2.5 py-1.5 mb-3"
              aria-label="Search tracked routes"
            />
            {filtered.length === 0 ? (
              <EmptyState title="No match" message={`No tracked route matches "${query}".`} />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border-strong text-left">
                      <th className="eyebrow font-semibold py-1.5">Route</th>
                      <th className="eyebrow font-semibold py-1.5">Region</th>
                      <th className="eyebrow font-semibold py-1.5 text-right">Route Index</th>
                      <th className="eyebrow font-semibold py-1.5">Pressure</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((p) => (
                      <tr key={p.route_code} className="border-b border-border-subtle hover:bg-panel-alt/50">
                        <td className="py-2">
                          <Link href={`/routes/${p.route_code}`} className="font-medium text-primary hover:text-accent mono">{p.route_code}</Link>
                          <div className="text-[11px] text-muted">{p.origin_city} → {p.destination_city}</div>
                        </td>
                        <td className="py-2 text-secondary">{p.region}</td>
                        <td className="py-2 text-right numeric font-medium">{num(p.index_value, 1)}</td>
                        <td className="py-2">
                          <span className="inline-flex items-center gap-1.5">
                            <span className={cn("h-2 w-2 rounded-full inline-block", PRESSURE_DOT[p.pressure])} />
                            {p.pressure}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </PanelShell>
        </>
      )}
    </div>
  );
}
