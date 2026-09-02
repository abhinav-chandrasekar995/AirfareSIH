import { cn } from "@/lib/utils";

const STYLES: Record<string, string> = {
  CRITICAL: "bg-sev-critical text-white",
  HIGH: "bg-sev-high text-white",
  MEDIUM: "bg-[var(--warn-100)] text-[var(--warn-700)] border border-[var(--warn-400)]",
  LOW: "bg-[var(--info-100)] text-[var(--info-600)]",
};

// Severity is also encoded by a left border on the row, so it survives greyscale and
// colour-blind viewing (not colour-only).
export function SeverityBadge({ severity, className }: { severity: string; className?: string }) {
  return (
    <span className={cn("inline-flex items-center rounded-sm px-1.5 py-0.5 text-[10.5px] font-mono font-bold uppercase tracking-wide", STYLES[severity] ?? STYLES.LOW, className)}>
      {severity}
    </span>
  );
}
