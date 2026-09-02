import type { Factor } from "@/types/api";

const COLORS = ["var(--series-6)", "var(--series-3)", "var(--series-4)", "var(--series-5)", "var(--grey-400)"];

// Anomaly factor attribution. Always sums to 100% (enforced server-side); the
// "Model-based attribution" note is rendered non-optionally beneath the bars.
export function AttributionBars({ factors, note }: { factors: Factor[]; note: string }) {
  return (
    <div>
      <div className="space-y-2">
        {factors.map((f, i) => (
          <div key={f.factor} className="flex items-center gap-2">
            <span className="text-xs text-secondary w-40 shrink-0 truncate">{f.label}</span>
            <div className="flex-1 h-3 bg-panel-alt rounded-sm overflow-hidden">
              <div className="h-full rounded-sm" style={{ width: `${f.pct}%`, background: COLORS[i % COLORS.length] }} />
            </div>
            <span className="text-xs numeric w-10 text-right">{f.pct.toFixed(0)}%</span>
          </div>
        ))}
      </div>
      <p className="text-[11px] text-muted mt-3 italic">{note}</p>
    </div>
  );
}
