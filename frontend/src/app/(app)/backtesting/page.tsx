"use client";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { KpiCard } from "@/components/kpi/KpiCard";
import { EmptyState, ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { BenchmarkOverlayChart } from "@/components/charts/BenchmarkOverlayChart";
import { ResidualChart } from "@/components/charts/ResidualChart";
import { MospiComparisonChart } from "@/components/charts/MospiComparisonChart";
import { useBacktest, useMospiComparison } from "@/lib/api/hooks";
import { num, istDate } from "@/lib/format";

export default function BacktestingPage() {
  const { data, isLoading, isError, error } = useBacktest();
  const { data: mospi, isLoading: loadingMospi } = useMospiComparison();

  return (
    <div>
      <PageHeader title="Backtesting Lab" subtitle="Our index validated against the real MoSPI Airfare CPI, with an illustrative DGCA scenario below" />

      {loadingMospi ? (
        <Skeleton className="h-80" />
      ) : mospi?.data ? (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
            <KpiCard
              label="Correlation vs MoSPI"
              value={mospi.data.overlap_metrics ? num(mospi.data.overlap_metrics.correlation, 2) : "—"}
              context={`${mospi.data.overlap_months} real overlapping months`}
            />
            <KpiCard
              label="MAPE vs MoSPI"
              value={mospi.data.overlap_metrics ? `${num(mospi.data.overlap_metrics.mape, 1)}%` : "—"}
            />
            <KpiCard label="Data Lag Advantage" value={`+${mospi.data.data_lag_days}d`} context="ahead of official release" />
            <KpiCard label="Rebase Anchor" value={mospi.data.anchor_month.slice(0, 7)} context={`scale ${num(mospi.data.scale_factor, 3)}`} />
          </div>

          <PanelShell
            title="Our Nowcasted APIx vs the Real MoSPI Airfare CPI"
            source={`cpi_reference (vintage ${mospi.data.series_vintage})`}
            info={mospi.data.alignment_method}
            className="mb-4"
          >
            {mospi.data.points.length > 0 ? (
              <MospiComparisonChart
                points={mospi.data.points}
                lastOfficialMonth={mospi.data.last_official_month}
                dataLagDays={mospi.data.data_lag_days}
              />
            ) : (
              <EmptyState title="No comparison data" message="No overlapping months between our index and MoSPI's series." />
            )}
          </PanelShell>
        </>
      ) : (
        <EmptyState title="No MoSPI reference data" message="Run scripts/ingest_mospi_cpi.py to load the real MoSPI Airfare CPI series." />
      )}

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
