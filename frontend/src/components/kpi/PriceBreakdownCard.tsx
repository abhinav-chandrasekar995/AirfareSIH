"use client";
import { inr, num } from "@/lib/format";
import type { PriceBreakdown } from "@/types/api";

// Base fare vs taxes+fees as a proportion of the total, the concrete number behind the
// Core/Headline split: Core APIx tracks only the base-fare bar, Headline tracks the
// whole thing. See RBI_APIX_MODULE_LOG.md §2.
export function PriceBreakdownCard({ data }: { data: PriceBreakdown }) {
  const base = data.avg_base_fare ?? 0;
  const taxes = data.avg_taxes_and_fees ?? 0;
  const total = data.avg_total_fare ?? (base + taxes || 1);
  const basePct = (base / total) * 100;
  const taxesPct = 100 - basePct;

  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-[11px] font-mono uppercase tracking-wide text-muted">Avg Base Fare</span>
        <span className="text-sm font-bold numeric text-primary">{inr(data.avg_base_fare)}</span>
      </div>
      <div className="flex items-baseline justify-between mb-3">
        <span className="text-[11px] font-mono uppercase tracking-wide text-muted">Avg Taxes &amp; Fees</span>
        <span className="text-sm font-bold numeric text-secondary">{inr(data.avg_taxes_and_fees)}</span>
      </div>

      <div className="h-3 w-full rounded-sm overflow-hidden flex border border-border-subtle" role="img" aria-label={`Base fare ${num(basePct, 0)}% of total, taxes and fees ${num(taxesPct, 0)}%`}>
        <div style={{ width: `${basePct}%`, background: "var(--interactive-primary)" }} />
        <div style={{ width: `${taxesPct}%`, background: "var(--warn-400)" }} />
      </div>
      <div className="flex items-center justify-between mt-1.5 text-[10.5px] text-muted">
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full inline-block" style={{ background: "var(--interactive-primary)" }} /> Base ({num(basePct, 0)}%)</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full inline-block" style={{ background: "var(--warn-400)" }} /> Taxes &amp; fees ({num(taxesPct, 0)}%)</span>
      </div>

      <div className="mt-3 pt-3 border-t border-border-subtle flex items-baseline justify-between">
        <span className="text-[11px] font-mono uppercase tracking-wide text-muted">Avg Total Fare</span>
        <span className="text-base font-extrabold numeric text-primary">{inr(data.avg_total_fare)}</span>
      </div>
    </div>
  );
}
