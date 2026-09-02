"use client";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { KpiCard, HeroKpi } from "@/components/kpi/KpiCard";
import { PanelShell } from "@/components/panels/PanelShell";
import { EmptyState, ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { IndexTrendChart } from "@/components/charts/IndexTrendChart";
import { AirfareGlobe } from "@/components/charts/AirfareGlobe";
import { MoversList } from "@/components/tables/MoversList";
import { useDashboard, useIndexSeries } from "@/lib/api/hooks";
import { compactNum, istDate, num } from "@/lib/format";
import { AlertTriangle, Info, Maximize2 } from "lucide-react";

export default function DashboardPage() {
  const { data: dash, isLoading, isError, error } = useDashboard();
  const { data: series } = useIndexSeries("NATIONAL");

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
        <Skeleton className="h-72" />
      </div>
    );
  }

  if (isError || !dash) {
    return <ErrorState message={error instanceof Error ? error.message : "The dashboard could not be loaded."} />;
  }

  const d = dash.data;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle={`National airfare measurement — vintage ${d.as_of ? istDate(d.as_of) : "—"}`}
      />

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3 mb-4">
        <div className="col-span-2">
          <HeroKpi
            label="India Airfare Index"
            value={num(d.index_value, 1)}
            delta={d.index_change_mom_pct}
            context={`base ${istDate(d.base_period)}=100`}
          />
        </div>
        <KpiCard label="Routes Tracked" value={String(d.routes_tracked)} href="/routes" />
        <KpiCard label="Airlines" value={String(d.airlines_tracked)} href="/airlines" />
        <KpiCard label="OTA Sources" value={String(d.ota_sources)} href="/collection" />
        <KpiCard label="Data Points" value={compactNum(d.total_data_points)} href="/data-explorer" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 mb-4">
        <div className="lg:col-span-8">
          <PanelShell
            title="Airfare Index Trend"
            info="India Airfare Index across the tracked basket, computed daily from quality-filtered observations."
            source="index_values"
            count={series?.data.length}
            qualityThreshold={series?.meta.quality_threshold}
          >
            {series && series.data.length > 0 ? (
              <IndexTrendChart points={series.data} label="India Airfare Index" />
            ) : (
              <EmptyState title="Index not yet available" message="No index values have been computed for this period." />
            )}
          </PanelShell>
        </div>
        <div className="lg:col-span-4">
          <PanelShell
            title="Airfare Pressure Map"
            info="Route-level price pressure vs the index base, plotted as airway lines on a globe centred on India."
            source="index_values, routes"
            count={d.pressure_map.length}
            actions={
              <Link
                href="/pressure-map"
                className="flex items-center gap-1 text-[11px] font-mono uppercase tracking-wide text-accent hover:underline"
              >
                <Maximize2 size={12} /> Expand
              </Link>
            }
          >
            <Link href="/pressure-map" className="block group" aria-label="Open the full interactive pressure map">
              <div className="transition-transform duration-150 group-hover:-translate-x-0.5 group-hover:-translate-y-0.5">
                <AirfareGlobe points={d.pressure_map} interactive={false} />
              </div>
              <p className="mt-2 text-center text-[11px] text-muted">Click to open the full interactive map</p>
            </Link>
          </PanelShell>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-4">
          <PanelShell title="Top Price Increases" subtitle="7-day change" source="route index" count={d.top_increases.length}>
            <MoversList movers={d.top_increases} />
          </PanelShell>
        </div>
        <div className="lg:col-span-4">
          <PanelShell title="Top Price Decreases" subtitle="7-day change" source="route index" count={d.top_decreases.length}>
            <MoversList movers={d.top_decreases} />
          </PanelShell>
        </div>
        <div className="lg:col-span-4">
          <PanelShell title="Key Insights" subtitle="Generated from computed statistics" source="dashboard analytics" count={d.insights.length}>
            {d.insights.length === 0 ? (
              <EmptyState title="No insights yet" message="Insights appear once sufficient history has accumulated." />
            ) : (
              <ul className="space-y-3">
                {d.insights.map((insight) => (
                  <li key={insight.id} className="flex items-start gap-2 text-xs">
                    {insight.severity === "warning" ? (
                      <AlertTriangle size={14} className="text-[var(--warn-600)] shrink-0 mt-0.5" />
                    ) : (
                      <Info size={14} className="text-[var(--info-600)] shrink-0 mt-0.5" />
                    )}
                    <span className="text-secondary leading-relaxed">
                      {insight.href ? (
                        <Link href={insight.href} className="hover:text-accent">{insight.text}</Link>
                      ) : (
                        insight.text
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </PanelShell>
        </div>
      </div>
    </div>
  );
}
