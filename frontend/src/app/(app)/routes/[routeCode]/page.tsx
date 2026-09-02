"use client";
import { useParams } from "next/navigation";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { PanelShell } from "@/components/panels/PanelShell";
import { KpiCard } from "@/components/kpi/KpiCard";
import { EmptyState, ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { FareTrendChart } from "@/components/charts/FareTrendChart";
import { FareCompositionBar } from "@/components/charts/FareCompositionBar";
import { SourceSpreadChart } from "@/components/charts/SourceSpreadChart";
import { useRoute } from "@/lib/api/hooks";
import { inr, num, pct } from "@/lib/format";
import { cn } from "@/lib/utils";

const VOL_COLOR: Record<string, string> = { HIGH: "text-sev-high", MEDIUM: "text-sev-medium", LOW: "text-sev-low" };

export default function RouteDetailPage() {
  const params = useParams<{ routeCode: string }>();
  const code = String(params.routeCode).toUpperCase();
  const { data, isLoading, isError, error } = useRoute(code);

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError || !data) return <ErrorState message={error instanceof Error ? error.message : `Route '${code}' could not be loaded.`} />;

  const r = data.data;

  return (
    <div>
      <Breadcrumbs items={[{ label: "Home", href: "/dashboard" }, { label: "Routes", href: "/routes" }, { label: code }]} />
      <PageHeader
        title={`${r.origin} → ${r.destination}`}
        subtitle={`${r.origin_city} (${r.origin_airport}) → ${r.destination_city} (${r.destination_airport}) · ${r.region} · ${r.distance_km ? `${r.distance_km} km` : ""}`}
        actions={
          <div className="flex gap-2">
            <Link href={`/lead-time?route=${code}`} className="text-xs text-accent hover:underline">Lead-time →</Link>
            <Link href={`/anomalies?route=${code}`} className="text-xs text-accent hover:underline">Anomalies →</Link>
            <Link href={`/data-explorer?route=${code}`} className="text-xs text-accent hover:underline">Data Explorer →</Link>
          </div>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
        <KpiCard label="Current Fare" value={inr(r.current_fare)} />
        <KpiCard label="7-Day Avg" value={inr(r.avg_7d)} />
        <KpiCard label="30-Day Avg" value={inr(r.avg_30d)} />
        <KpiCard label="Yearly Avg" value={inr(r.avg_yearly)} />
        <KpiCard label="Route Index" value={num(r.route_index, 1)} delta={r.change_mom_pct} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-1 gap-4 mb-4">
        <PanelShell title="Fare Trend" source="fare_observations" count={r.trend.length}>
          {r.trend.length > 0 ? <FareTrendChart points={r.trend} /> : <EmptyState title="No trend data" message="Not enough observations yet." />}
        </PanelShell>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <PanelShell title="Airline Comparison" source="fare_observations" count={r.airlines.length}>
          {r.airlines.length === 0 ? (
            <EmptyState title="No airline data" message="No airline breakdown available." />
          ) : (
            <table className="w-full text-xs numeric">
              <tbody>
                {r.airlines.map((a) => (
                  <tr key={a.airline_code} className="border-b border-border-subtle">
                    <td className="py-1.5">{a.airline}</td>
                    <td className="py-1.5 text-right">{inr(a.median_fare)}</td>
                    <td className="py-1.5 text-right text-muted w-16">n={a.n_observations}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </PanelShell>

        <PanelShell title="OTA / Source Comparison" source="fare_observations" count={r.sources.length}>
          <SourceSpreadChart sources={r.sources} />
        </PanelShell>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <PanelShell title="Fare Composition" info="Base fare + taxes + UDF + airport charges + convenience fee = total consumer fare" source="fare_observations">
          {r.composition ? <FareCompositionBar composition={r.composition} /> : <EmptyState title="No composition data" message="Fare component breakdown unavailable." />}
        </PanelShell>

        <PanelShell title="Route Risk Profile" source="volatility_metrics, anomalies">
          {r.volatility ? (
            <dl className="text-xs space-y-2">
              <div className="flex justify-between border-b border-border-subtle py-1.5">
                <dt className="text-muted">Volatility score</dt>
                <dd className={cn("font-semibold", VOL_COLOR[r.volatility.volatility_score])}>{r.volatility.volatility_score}</dd>
              </div>
              <div className="flex justify-between border-b border-border-subtle py-1.5">
                <dt className="text-muted">Coefficient of variation</dt>
                <dd className="numeric">{num(r.volatility.coefficient_of_variation, 3)}</dd>
              </div>
              <div className="flex justify-between border-b border-border-subtle py-1.5">
                <dt className="text-muted">Std. deviation</dt>
                <dd className="numeric">{inr(r.volatility.std_dev)}</dd>
              </div>
              <div className="flex justify-between py-1.5">
                <dt className="text-muted">Abnormal move frequency</dt>
                <dd className="numeric">{pct(r.volatility.abnormal_move_frequency, 1, false)}</dd>
              </div>
            </dl>
          ) : (
            <EmptyState title="No volatility data" message="Volatility has not been computed for this route." />
          )}
        </PanelShell>
      </div>
    </div>
  );
}
