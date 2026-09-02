"use client";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { FilterBar } from "@/components/filters/FilterBar";
import { EmptyState, Skeleton } from "@/components/panels/EmptyState";
import { LeadTimeCurveChart } from "@/components/charts/LeadTimeCurveChart";
import { useLeadTime, useRoutes } from "@/lib/api/hooks";
import { pct, num } from "@/lib/format";

export default function LeadTimePageInner() {
  const search = useSearchParams();
  const [route, setRoute] = useState(search.get("route") ?? "");
  const { data: routes } = useRoutes();
  const { data, isLoading } = useLeadTime(route || undefined);

  return (
    <div>
      <PageHeader title="Lead-Time Intelligence" subtitle="How advance-purchase timing drives fare — T+1 through T+45" />

      <FilterBar>
        <select value={route} onChange={(e) => setRoute(e.target.value)} className="text-xs bg-panel border border-border-subtle rounded-md px-2 py-1.5">
          <option value="">All routes (national curve)</option>
          {routes?.data.map((r) => <option key={r.route_code} value={r.route_code}>{r.route_code}</option>)}
        </select>
      </FilterBar>

      {isLoading || !data ? (
        <Skeleton className="h-96 mt-3" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 mt-3">
          <div className="lg:col-span-8">
            <PanelShell title="Lead-Time Fare Curve" source="fare_observations" count={data.data.curve.reduce((s, p) => s + p.n_observations, 0)} info={data.data.method_note}>
              {data.data.curve.length > 0 ? <LeadTimeCurveChart points={data.data.curve} /> : <EmptyState title="No curve data" message="Not enough observations across booking windows." />}
            </PanelShell>
          </div>
          <div className="lg:col-span-4">
            <PanelShell title="Booking Window Table" source="fare_observations">
              <table className="w-full text-xs numeric mb-4">
                <tbody>
                  {data.data.curve.map((p) => (
                    <tr key={p.lead_bucket} className="border-b border-border-subtle">
                      <td className="py-1.5">T+{p.lead_days}</td>
                      <td className="py-1.5 text-right">₹{p.avg_fare.toLocaleString("en-IN")}</td>
                      <td className="py-1.5 text-right text-muted">{p.vs_earliest_pct !== null ? pct(p.vs_earliest_pct) : "baseline"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <dl className="text-xs space-y-2">
                <div className="flex justify-between border-b border-border-subtle py-1.5">
                  <dt className="text-muted">Last-minute premium</dt>
                  <dd className="numeric font-medium">{data.data.last_minute_premium_pct !== null ? pct(data.data.last_minute_premium_pct) : "—"}</dd>
                </div>
                <div className="flex justify-between border-b border-border-subtle py-1.5">
                  <dt className="text-muted">Early-booking advantage</dt>
                  <dd className="numeric font-medium">{data.data.early_booking_advantage_pct !== null ? pct(data.data.early_booking_advantage_pct, 1, false) : "—"}</dd>
                </div>
                <div className="flex justify-between border-b border-border-subtle py-1.5">
                  <dt className="text-muted">Elasticity</dt>
                  <dd className="numeric font-medium">{data.data.elasticity !== null ? num(data.data.elasticity, 3) : "—"}</dd>
                </div>
                <div className="flex justify-between py-1.5">
                  <dt className="text-muted">Booking pressure</dt>
                  <dd className="font-semibold">{data.data.booking_pressure ?? "—"}</dd>
                </div>
              </dl>
            </PanelShell>
          </div>
          <div className="lg:col-span-12">
            <PanelShell title="Elasticity by Route" source="leadtime_curves" count={data.data.by_route.length}>
              {data.data.by_route.length === 0 ? (
                <EmptyState title="No route-level curves yet" message="Elasticity has not been computed per route." />
              ) : (
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border-strong text-left">
                      <th className="eyebrow font-semibold py-1.5">Route</th>
                      <th className="eyebrow font-semibold py-1.5 text-right">Elasticity</th>
                      <th className="eyebrow font-semibold py-1.5 text-right">Last-min premium</th>
                      <th className="eyebrow font-semibold py-1.5">Booking pressure</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.data.by_route.map((row) => (
                      <tr key={row.route_code} className="border-b border-border-subtle">
                        <td className="py-1.5 mono">{row.route_code}</td>
                        <td className="py-1.5 text-right numeric">{row.elasticity !== null ? num(row.elasticity, 3) : "—"}</td>
                        <td className="py-1.5 text-right numeric">{row.last_minute_premium_pct !== null ? pct(row.last_minute_premium_pct) : "—"}</td>
                        <td className="py-1.5 font-medium">{row.booking_pressure ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </PanelShell>
          </div>
        </div>
      )}
    </div>
  );
}
