"use client";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { EmptyState, ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { ForecastChart } from "@/components/charts/ForecastChart";
import { useForecast } from "@/lib/api/hooks";
import { inr } from "@/lib/format";
import { cn } from "@/lib/utils";

const BAND_COLOR: Record<string, string> = { HIGH: "text-sev-high", MEDIUM: "text-sev-medium", LOW: "text-sev-low" };

export default function ForecastPage() {
  const { data, isLoading, isError, error } = useForecast("NATIONAL");

  return (
    <div>
      <PageHeader title="Forecasting" subtitle="14-day ahead national airfare index, with prediction intervals" />

      {isLoading ? (
        <Skeleton className="h-96" />
      ) : isError || !data ? (
        <ErrorState message={error instanceof Error ? error.message : "No forecast has been generated yet."} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-8">
            <PanelShell title={`${data.data.horizon_days}-Day Forecast With Intervals`} source="forecasts" info="A point forecast is never shown without its prediction interval.">
              {data.data.points.length > 0 ? <ForecastChart points={data.data.points} /> : <EmptyState title="No forecast" message="Insufficient history to forecast." />}
            </PanelShell>
          </div>
          <div className="lg:col-span-4">
            <PanelShell title="Expected Airfare Pressure" source={`model: ${data.data.model_name}`}>
              <div className="text-center py-4">
                <div className={cn("text-3xl font-bold tracking-wide", BAND_COLOR[data.data.pressure_band])}>{data.data.pressure_band}</div>
                <div className="text-xs text-muted mt-2">Forecast range</div>
                <div className="text-sm numeric font-medium mt-1">{inr(data.data.forecast_range[0])} – {inr(data.data.forecast_range[1])}</div>
                <div className="text-[11px] text-muted mt-3">Model: {data.data.model_name} ({data.data.model_version})</div>
                <div className="text-[11px] text-muted">Confidence level: {(data.data.confidence_level * 100).toFixed(0)}%</div>
              </div>
            </PanelShell>
          </div>
        </div>
      )}
    </div>
  );
}
