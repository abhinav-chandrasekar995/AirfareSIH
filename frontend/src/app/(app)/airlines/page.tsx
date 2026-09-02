"use client";
import Link from "next/link";
import { Plane } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { EmptyState, ErrorState, Skeleton } from "@/components/panels/EmptyState";
import { useAirlines } from "@/lib/api/hooks";
import { cn } from "@/lib/utils";

// Fixed series-colour assignment, matching the design doc's rule that a carrier keeps
// the same colour on every screen (design doc Sec.2.3) - reused here for a coloured
// dot per airline card rather than a generic icon.
const CARRIER_COLOR: Record<string, string> = {
  "6E": "var(--series-1)", AI: "var(--series-6)", IX: "var(--series-3)",
  QP: "var(--series-4)", SG: "var(--series-5)",
};

export default function AirlinesPage() {
  const { data, isLoading, isError, error } = useAirlines();

  return (
    <div>
      <PageHeader title="Airlines" subtitle="Every carrier tracked by the collection engine" />
      <PanelShell title="Airline Directory" source="airlines" count={data?.data.length}>
        {isLoading ? (
          <Skeleton className="h-64" />
        ) : isError ? (
          <ErrorState message={error instanceof Error ? error.message : "Could not load airlines."} />
        ) : !data || data.data.length === 0 ? (
          <EmptyState title="No airlines tracked" message="No carriers are active in the collection basket." />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.data.map((a) => (
              <Link
                key={a.airline_code}
                href={`/data-explorer?airline=${a.airline_code}`}
                className="panel reveal p-4 flex items-center gap-3 hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[var(--shadow-hard-md)] transition-transform duration-150"
              >
                <span
                  className="h-10 w-10 border-[var(--border-hard)] border-border-strong flex items-center justify-center shrink-0"
                  style={{ background: CARRIER_COLOR[a.airline_code] ?? "var(--series-8)" }}
                >
                  <Plane size={18} className="text-white" strokeWidth={2.5} />
                </span>
                <div className="min-w-0">
                  <div className="font-extrabold text-sm uppercase tracking-tight text-primary truncate">{a.name}</div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="mono text-[11px] text-muted">{a.airline_code}</span>
                    <span
                      className={cn(
                        "text-[10px] font-mono font-bold uppercase px-1.5 py-0.5 border-[1.5px]",
                        a.airline_type === "FSC" ? "border-[var(--series-4)] text-[var(--series-4)]" : "border-[var(--series-5)] text-[var(--series-5)]",
                      )}
                    >
                      {a.airline_type === "FSC" ? "Full Service" : "Low Cost"}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </PanelShell>
    </div>
  );
}
