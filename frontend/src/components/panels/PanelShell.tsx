"use client";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";

// PanelShell REQUIRES source, count and qualityThreshold - the design principle that
// every data panel declares its provenance is compiled in, not left to discipline.
export function PanelShell({
  title, subtitle, children, actions, source, count, qualityThreshold, info, className, id,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  source: string;
  count?: number | null;
  qualityThreshold?: number;
  info?: string;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={cn("panel reveal flex flex-col", className)}>
      <header className="flex items-start justify-between gap-3 border-b-[var(--border-hard)] border-border-strong px-4 py-2.5">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <h3 className="text-[15px] font-extrabold uppercase tracking-tight text-primary truncate">{title}</h3>
            {info && (
              <span title={info} className="text-muted cursor-help" aria-label={info}>
                <Info size={13} strokeWidth={2.25} />
              </span>
            )}
          </div>
          {subtitle && <p className="text-xs text-muted mt-0.5">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-1.5 shrink-0">{actions}</div>}
      </header>
      <div className="flex-1 p-4">{children}</div>
      <footer className="border-t-[var(--border-hard)] border-border-strong px-4 py-1.5 text-[11px] font-mono text-muted flex flex-wrap items-center gap-x-3 gap-y-0.5">
        <span>Source: {source}</span>
        {count !== undefined && count !== null && <span>· n={count.toLocaleString("en-IN")}</span>}
        {qualityThreshold !== undefined && <span>· quality ≥ {qualityThreshold}</span>}
      </footer>
    </section>
  );
}
