"use client";
import Link from "next/link";
import { DeltaChip } from "@/components/badges/DeltaChip";
import { cn } from "@/lib/utils";

export function KpiCard({
  label, value, delta, deltaBasis, context, href, className,
}: {
  label: string;
  value: string;
  delta?: number | null;
  deltaBasis?: string;
  context?: string;
  href?: string;
  className?: string;
}) {
  const body = (
    <div
      className={cn(
        "panel reveal p-4 h-full transition-transform duration-150",
        href && "cursor-pointer hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[var(--shadow-hard-md)]",
        className,
      )}
    >
      <div className="eyebrow">{label}</div>
      <div className="mt-2 text-[34px] leading-none font-extrabold text-primary numeric">{value}</div>
      <div className="mt-2 flex items-center gap-2 flex-wrap">
        {delta !== undefined && <DeltaChip value={delta ?? null} basis={deltaBasis ?? "MoM"} />}
        {context && <span className="text-[11px] text-muted">{context}</span>}
      </div>
    </div>
  );
  return href ? <Link href={href} className="block h-full">{body}</Link> : body;
}

// Dark-inverted block, deliberately mirroring the marketing home page's hero index
// panel (HomeContent.tsx) - same India Airfare Index number, same visual treatment,
// so the figure reads as literally the same object whichever page it's viewed on.
// Colours are hardcoded to the unscoped --navy-950/--amber-500/--signal-* tokens
// (always defined at :root, unlike the marketing-only --b-* variables) so the block
// stays dark in both light and dark app themes, exactly like the marketing hero panel.
export function HeroKpi({ value, label, delta, context, sparkline }: { value: string; label: string; delta?: number | null; context?: string; sparkline?: React.ReactNode }) {
  return (
    <div
      className="reveal h-full flex flex-col justify-between p-5 border-[var(--border-hard)] border-[var(--navy-950)]"
      style={{ background: "var(--navy-950)", color: "var(--navy-100)", boxShadow: "var(--shadow-hard-md)" }}
    >
      <div className="text-[10.5px] font-mono font-bold uppercase tracking-wide" style={{ color: "var(--amber-500)" }}>
        {label}
      </div>
      <div className="mt-2">
        <div className="text-[56px] leading-none font-extrabold numeric" style={{ color: "var(--navy-50)" }}>{value}</div>
        <div className="mt-3 flex items-center gap-2 flex-wrap">
          {delta !== undefined && delta !== null && (
            <span className="font-mono text-xs font-bold uppercase tracking-wide" style={{ color: "var(--signal-500)" }}>
              {delta > 0 ? "▲" : delta < 0 ? "▼" : "–"} {Math.abs(delta).toFixed(1)}% MoM
            </span>
          )}
          {context && <span className="text-xs opacity-60">{context}</span>}
        </div>
      </div>
      {sparkline && <div className="mt-3 h-12">{sparkline}</div>}
    </div>
  );
}
