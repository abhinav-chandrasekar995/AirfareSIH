"use client";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { SeverityBadge } from "@/components/badges/SeverityBadge";
import { AttributionBars } from "@/components/charts/AttributionBars";
import { ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { useAnomaly } from "@/lib/api/hooks";
import { inr, pct, istDateTime } from "@/lib/format";

export default function AnomalyDetailPage() {
  const params = useParams<{ anomalyId: string }>();
  const id = Number(params.anomalyId);
  const { data, isLoading, isError, error } = useAnomaly(id);

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError || !data) return <ErrorState message={error instanceof Error ? error.message : "Anomaly not found."} />;

  const a = data.data;

  return (
    <div>
      <Breadcrumbs items={[{ label: "Home", href: "/dashboard" }, { label: "Anomalies", href: "/anomalies" }, { label: `#${a.anomaly_id}` }]} />
      <PageHeader
        title={`${a.route_code} — ${a.origin_city} → ${a.destination_city}`}
        subtitle={istDateTime(a.detected_at)}
        actions={<SeverityBadge severity={a.severity} />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <PanelShell title="Expected vs Observed" source="anomalies">
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center p-4 rounded-md bg-panel-alt">
              <div className="eyebrow">Expected</div>
              <div className="text-2xl font-semibold numeric mt-1">{inr(a.expected_fare)}</div>
              <div className="text-[11px] text-muted mt-1">{a.lead_bucket ? `T+${a.lead_bucket.replace("T", "")} baseline` : "baseline"}</div>
            </div>
            <div className="text-center p-4 rounded-md bg-panel-alt">
              <div className="eyebrow">Observed</div>
              <div className="text-2xl font-semibold numeric mt-1">{inr(a.observed_fare)}</div>
              <div className="text-[11px] text-muted mt-1">this observation</div>
            </div>
          </div>
          <div className="flex items-center justify-between mt-4 pt-3 border-t border-border-subtle text-sm">
            <span className="text-muted">Deviation</span>
            <span className="font-semibold numeric text-price-up">{pct(a.deviation_pct)}</span>
          </div>
          <div className="flex items-center justify-between mt-1.5 text-xs">
            <span className="text-muted">Detectors fired</span>
            <span className="numeric">{a.detectors_fired.join(", ") || "—"}</span>
          </div>
        </PanelShell>

        <PanelShell title="Contributing Factors" source="anomaly attribution model">
          <AttributionBars factors={a.factor_attribution} note={a.attribution_note} />
        </PanelShell>
      </div>

      <div className="flex gap-3">
        <Link href={`/routes/${a.route_code}`} className="text-xs text-accent hover:underline">View route intelligence →</Link>
        <Link href={`/lead-time?route=${a.route_code}`} className="text-xs text-accent hover:underline">View lead-time curve →</Link>
        <Link href={`/data-explorer?route=${a.route_code}`} className="text-xs text-accent hover:underline">View contributing observations →</Link>
      </div>
    </div>
  );
}
