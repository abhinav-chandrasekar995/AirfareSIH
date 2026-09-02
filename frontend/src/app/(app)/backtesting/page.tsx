"use client";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { KpiCard } from "@/components/kpi/KpiCard";
import { EmptyState, ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { BenchmarkOverlayChart } from "@/components/charts/BenchmarkOverlayChart";
import { ResidualChart } from "@/components/charts/ResidualChart";
import { useBacktest } from "@/lib/api/hooks";
import { num, istDate } from "@/lib/format";

export default function BacktestingPage() {
  const { data, isLoading, isError, error } = useBacktest();

  return (
    <div>
      <PageHeader title="Backtesting Lab" subtitle="Our index validated against the DGCA benchmark, out-of-sample" />

      {isLoading ? (
        <Skeleton className="h-96" />
      ) : isError || !data ? (
        <ErrorState message={error instanceof Error ? error.message : "No back-test run is available."} />
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
            <KpiCard label="Correlation" value={num(data.data.correlation, 2)} />
            <KpiCard label="MAPE" value={`${num(data.data.mape, 1)}%`} />
            <KpiCard label="MAE" value={num(data.data.mae, 0)} />
            <KpiCard label="RMSE" value={num(data.data.rmse, 0)} />
            <KpiCard label="Directional Accuracy" value={`${num(data.data.directional_accuracy, 0)}%`} />
          </div>

          <PanelShell
            title="Our Index vs DGCA Benchmark"
            subtitle={`${data.data.n_test_days}-day out-of-sample test window: ${istDate(data.data.test_start)} to ${istDate(data.data.test_end)}`}
            source={`DGCA benchmark (vintage ${data.data.dgca_vintage})`}
            info={data.data.alignment_method}
            className="mb-4"
          >
            {data.data.series.length > 0 ? (
              <BenchmarkOverlayChart series={data.data.series} splitIndex={Math.floor(data.data.series.length / 2)} />
            ) : (
              <EmptyState title="No series data" message="No aligned monthly series available." />
            )}
          </PanelShell>

          <PanelShell title="Residuals" subtitle="Our index minus DGCA benchmark, by month" source="backtest_runs">
            {data.data.series.length > 0 ? (
              <ResidualChart series={data.data.series} />
            ) : (
              <EmptyState title="No residual data" message="No aligned monthly series available." />
            )}
          </PanelShell>
        </>
      )}
    </div>
  );
}
