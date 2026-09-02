"use client";
import { PageHeader } from "@/components/layout/PageHeader";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { PanelShell } from "@/components/panels/PanelShell";
import { useMethodology } from "@/lib/api/hooks";
import { istDate, pct } from "@/lib/format";
import { Skeleton } from "@/components/panels/EmptyState";

export default function MethodologyPage() {
  const { data, isLoading } = useMethodology();

  return (
    <div>
      <Breadcrumbs items={[{ label: "Home", href: "/dashboard" }, { label: "Airfare Index", href: "/index-explorer" }, { label: "Methodology" }]} />
      <PageHeader title="Index Methodology" subtitle="Everything needed to reproduce a published index value" />

      {isLoading || !data ? (
        <Skeleton className="h-96" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <PanelShell title="Formulas" source="methodology_versions">
            <div className="space-y-3 text-xs">
              <div>
                <div className="eyebrow mb-1">Route index</div>
                <code className="block bg-inset p-2 rounded-md mono">{data.data.route_index_formula}</code>
              </div>
              <div>
                <div className="eyebrow mb-1">Aggregate index</div>
                <code className="block bg-inset p-2 rounded-md mono">{data.data.aggregate_formula}</code>
              </div>
              <div>
                <div className="eyebrow mb-1">Missing-route policy</div>
                <p className="text-secondary leading-relaxed">{data.data.missing_route_policy}</p>
              </div>
            </div>
          </PanelShell>

          <PanelShell title="Configuration" source="methodology_versions">
            <dl className="text-xs space-y-2">
              {[
                ["Methodology version", data.data.methodology_version],
                ["Base period", istDate(data.data.base_period)],
                ["Estimator", data.data.estimator.replace(/_/g, " ")],
                ["Quality threshold", `≥ ${data.data.quality_threshold}`],
                ["Min. observations / period", String(data.data.min_observations_per_period)],
                ["Weight set", data.data.weight_set_version ?? "—"],
                ["Weight source", data.data.weight_source ?? "—"],
                ["Basket size", `${data.data.basket_size} routes`],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between border-b border-border-subtle py-1.5">
                  <dt className="text-muted">{label}</dt>
                  <dd className="text-primary font-medium numeric">{value}</dd>
                </div>
              ))}
            </dl>
          </PanelShell>

          <PanelShell title="Route Weights" subtitle="DGCA passenger-traffic-derived, versioned" source="route_weights" count={data.data.weights.length} className="lg:col-span-2">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border-strong text-left">
                  <th className="eyebrow font-semibold py-1.5">Route</th>
                  <th className="eyebrow font-semibold py-1.5 text-right">Weight</th>
                  <th className="eyebrow font-semibold py-1.5">Source</th>
                </tr>
              </thead>
              <tbody>
                {data.data.weights.map((w) => (
                  <tr key={w.route_code} className="border-b border-border-subtle">
                    <td className="py-1.5 mono">{w.route_code}</td>
                    <td className="py-1.5 text-right numeric">{pct(w.weight * 100, 1, false)}</td>
                    <td className="py-1.5 text-muted">{w.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </PanelShell>
        </div>
      )}
    </div>
  );
}
