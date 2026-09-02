"use client";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { EmptyState, ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { useDataQuality } from "@/lib/api/hooks";
import { relativeTime, pct } from "@/lib/format";
import { cn } from "@/lib/utils";
import { AlertCircle } from "lucide-react";

const STATUS_COLOR: Record<string, string> = {
  ACTIVE: "bg-quality-high", DEGRADED: "bg-quality-medium", UNAVAILABLE: "bg-quality-low", DISABLED: "bg-grey-400",
};

export default function CollectionPage() {
  const { data, isLoading, isError, error } = useDataQuality();

  return (
    <div>
      <PageHeader title="Collection Engine" subtitle="Per-source adapter status, scheduler and data-quality flags" />

      {isLoading ? (
        <Skeleton className="h-96" />
      ) : isError || !data ? (
        <ErrorState message={error instanceof Error ? error.message : "Could not load collection health."} />
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
            {data.data.sources.map((s) => (
              <div key={s.source_code} className="panel p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-primary">{s.source_name}</span>
                  <span className="flex items-center gap-1.5 text-[11px]">
                    <span className={cn("h-1.5 w-1.5 rounded-full", STATUS_COLOR[s.status])} />
                    {s.status}
                  </span>
                </div>
                <div className="text-[11px] text-muted mb-2">{s.source_type === "AIRLINE_DIRECT" ? "Airline direct" : "OTA"} · rate limit {s.rate_limit_rpm}/min</div>
                <dl className="grid grid-cols-2 gap-1 text-[11px] numeric">
                  <div className="flex justify-between"><dt className="text-muted">Found</dt><dd>{s.records_found}</dd></div>
                  <div className="flex justify-between"><dt className="text-muted">Valid</dt><dd>{s.records_valid}</dd></div>
                  <div className="flex justify-between"><dt className="text-muted">Failed</dt><dd>{s.records_failed}</dd></div>
                  <div className="flex justify-between"><dt className="text-muted">Success</dt><dd>{pct(s.success_rate, 0, false)}</dd></div>
                </dl>
                <div className="text-[10px] text-muted mt-2">Last run: {s.last_run_at ? relativeTime(s.last_run_at) : "never (seeded demo)"}</div>
              </div>
            ))}
          </div>

          <PanelShell title="Data-Quality Flags" subtitle="Separated from market anomalies — scraper faults never register as price surges" source="data_quality_flags" count={data.data.flags.length}>
            {data.data.flags.length === 0 ? (
              <EmptyState title="No open flags" message="No data-quality issues have been raised." />
            ) : (
              <ul className="divide-y divide-border-subtle">
                {data.data.flags.map((f) => (
                  <li key={f.flag_id} className="flex items-start gap-2 py-2">
                    <AlertCircle size={14} className="text-[var(--warn-600)] shrink-0 mt-0.5" />
                    <div className="min-w-0">
                      <div className="text-xs font-medium text-primary">{f.flag_type} · {f.scope_ref}</div>
                      <div className="text-[11px] text-muted">{f.description}</div>
                      <div className="text-[10px] text-muted mt-0.5">{relativeTime(f.raised_at)} {f.resolved_at ? "· resolved" : "· open"}</div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </PanelShell>
        </>
      )}
    </div>
  );
}
