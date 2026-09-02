"use client";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { KpiCard } from "@/components/kpi/KpiCard";
import { EmptyState } from "@/components/panels/EmptyState";
import { IndexTrendChart } from "@/components/charts/IndexTrendChart";
import { useIndexSeries, useIndexSummary } from "@/lib/api/hooks";
import { num, istDate } from "@/lib/format";

const REGIONS = ["NORTH", "SOUTH", "EAST", "WEST"];

export default function IndexExplorerPage() {
  const { data: national } = useIndexSeries("NATIONAL");
  const { data: summary } = useIndexSummary();

  return (
    <div>
      <PageHeader
        title="Airfare Price Index"
        subtitle="The statistical heart of the platform"
        actions={<Link href="/index-explorer/methodology" className="text-xs text-accent hover:underline">View methodology →</Link>}
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <KpiCard
          label="National Index"
          value={num(summary?.data.headline?.current_value, 1)}
          delta={summary?.data.headline?.change_pct}
          context={summary?.data.headline ? `as of ${istDate(summary.data.headline.as_of)}` : undefined}
        />
        {REGIONS.map((r) => {
          const row = summary?.data.regional.find((x) => x.scope === r);
          return <KpiCard key={r} label={`${r.charAt(0)}${r.slice(1).toLowerCase()} India`} value={num(row?.current_value, 1)} />;
        })}
      </div>

      <PanelShell title="National Index Trend" source="index_values" count={national?.data.length} qualityThreshold={national?.meta.quality_threshold}>
        {national && national.data.length > 0 ? (
          <IndexTrendChart points={national.data} label="National Index" />
        ) : (
          <EmptyState title="No index history" message="Index values have not been computed yet." />
        )}
      </PanelShell>
    </div>
  );
}
