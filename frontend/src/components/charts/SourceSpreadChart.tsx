import { inr, pct } from "@/lib/format";
import type { SourceDivergence } from "@/types/api";
import { cn } from "@/lib/utils";

// Airline/OTA divergence: same itinerary priced across sources. Bar length encodes
// fare; the vs-direct delta is shown as text so it never depends on colour alone.
export function SourceSpreadChart({ sources }: { sources: SourceDivergence[] }) {
  if (sources.length === 0) return null;
  const max = Math.max(...sources.map((s) => s.avg_fare));

  return (
    <div className="space-y-2">
      {sources.map((s) => (
        <div key={s.source_code} className="flex items-center gap-2">
          <span className="text-xs text-secondary w-28 shrink-0 truncate">{s.source}</span>
          <div className="flex-1 h-4 bg-panel-alt rounded-sm overflow-hidden">
            <div
              className={cn("h-full rounded-sm", s.source_type === "AIRLINE_DIRECT" ? "bg-[var(--series-8)]" : "bg-[var(--series-1)]")}
              style={{ width: `${(s.avg_fare / max) * 100}%` }}
            />
          </div>
          <span className="text-xs numeric w-20 text-right">{inr(s.avg_fare)}</span>
          <span className={cn("text-[11px] numeric w-14 text-right", s.vs_direct_pct && s.vs_direct_pct > 0 ? "text-price-up" : "text-price-down")}>
            {s.vs_direct_pct !== null ? pct(s.vs_direct_pct) : "—"}
          </span>
        </div>
      ))}
    </div>
  );
}
