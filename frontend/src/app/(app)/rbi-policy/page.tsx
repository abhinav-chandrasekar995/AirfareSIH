"use client";
import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { KpiCard } from "@/components/kpi/KpiCard";
import { PriceBreakdownCard } from "@/components/kpi/PriceBreakdownCard";
import { ApixTrendChart } from "@/components/charts/ApixTrendChart";
import { InflationAlertBanner } from "@/components/rbi/InflationAlertBanner";
import { EmptyState, ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { useApixComparison, usePriceBreakdown, useApixAlert } from "@/lib/api/hooks";
import { num, pct } from "@/lib/format";
import { Download } from "lucide-react";
import { cn } from "@/lib/utils";

// RBI Policy & Elasticity Simulator (Module 2/3 of the RBI APIx proposal). Core vs
// Headline APIx toggle + policy-band chart, price breakdown, and the live inflation
// alert - all reading the /apix/* endpoints built alongside this page. Fuel-tax slider
// and lead-time-reweighted toggle were explicitly deferred, not built here - see
// RBI_APIX_MODULE_LOG.md §0 for why.
export default function RbiPolicyPage() {
  const [mode, setMode] = useState<"core" | "headline">("core");
  const { data: comparison, isLoading: loadingComparison, isError: errComparison, error: comparisonError } = useApixComparison();
  const { data: breakdown, isLoading: loadingBreakdown } = usePriceBreakdown();
  const { data: alert, isLoading: loadingAlert } = useApixAlert();

  const isLoading = loadingComparison || loadingBreakdown || loadingAlert;

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-14" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
        <Skeleton className="h-80" />
      </div>
    );
  }

  if (errComparison || !comparison || !alert) {
    return <ErrorState message={comparisonError instanceof Error ? comparisonError.message : "RBI APIx data could not be loaded."} />;
  }

  const points = mode === "core" ? comparison.data.core : comparison.data.headline;
  const coreLatest = comparison.data.core.at(-1) ?? null;
  const headlineLatest = comparison.data.headline.at(-1) ?? null;

  return (
    <div>
      <PageHeader
        title="RBI Policy & Elasticity Simulator"
        subtitle="Core vs Headline APIx against RBI inflation tolerance bands, with a live week-over-week alert"
      />

      <InflationAlertBanner alert={alert.data} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <KpiCard label="Core APIx" value={coreLatest ? num(coreLatest.index_value, 1) : "—"} context="base fare only" />
        <KpiCard label="Headline APIx" value={headlineLatest ? num(headlineLatest.index_value, 1) : "—"} context="total fare" />
        <KpiCard
          label="National WoW"
          value={alert.data.national_wow_pct !== null ? pct(alert.data.national_wow_pct) : "—"}
          context={`tolerance ±${num(alert.data.national_threshold_pct, 1)}%`}
        />
        <KpiCard
          label="Alert Status"
          value={alert.data.status === "HIGH_INFLATION_RISK" ? "High Risk" : "Normal"}
          context={alert.data.spiking_route ? `spike: ${alert.data.spiking_route}` : "no route spike"}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8">
          <PanelShell
            title="APIx Trend vs RBI Tolerance Bands"
            info="Core (base-fare) or Headline (total-fare) APIx over the last ~120 days, against reference lines at base +4% and +6%."
            source="core_index_values, index_values"
            count={points.length}
            actions={
              <div className="flex items-center border border-border-subtle rounded-md overflow-hidden text-[11px] font-mono uppercase tracking-wide">
                {(["core", "headline"] as const).map((m) => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    aria-pressed={mode === m}
                    className={cn(
                      "px-2.5 py-1 transition-colors",
                      mode === m ? "bg-interactive text-white" : "text-secondary hover:bg-panel-alt",
                    )}
                  >
                    {m === "core" ? "Core" : "Headline"}
                  </button>
                ))}
              </div>
            }
          >
            {points.length > 0 ? (
              <ApixTrendChart points={points} mode={mode} />
            ) : (
              <EmptyState title="No APIx data yet" message="The Core/Headline series has not been computed for this period." />
            )}
          </PanelShell>
        </div>

        <div className="lg:col-span-4">
          <PanelShell
            title="Price Breakdown"
            info="Average base fare vs taxes & fees, most recent day with observations."
            source="fare_observations"
            count={breakdown?.data.n_observations}
          >
            {breakdown?.data ? (
              <PriceBreakdownCard data={breakdown.data} />
            ) : (
              <EmptyState title="No breakdown available" message="No fare observations for the most recent date." />
            )}
          </PanelShell>

          <div className="mt-4">
            <a
              href="/backend/api/v1/reports/rbi-policy-brief"
              className="flex items-center justify-center gap-1.5 w-full text-xs font-bold uppercase tracking-wide bg-interactive text-white rounded-md px-3 py-2.5 hover:bg-interactive-hover"
            >
              <Download size={13} /> Generate RBI Policy Brief
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
