import { cn } from "@/lib/utils";
import { pct } from "@/lib/format";

// Direction convention: a rising fare is adverse (red), a falling fare benign (green).
export function DeltaChip({ value, basis = "MoM", className }: { value: number | null; basis?: string; className?: string }) {
  if (value === null || value === undefined) return <span className="text-muted numeric">—</span>;
  const flat = Math.abs(value) < 0.5;
  const up = value > 0;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 text-xs font-bold numeric",
        flat ? "bg-panel-alt text-price-flat" : up ? "bg-price-up-bg text-price-up" : "bg-price-down-bg text-price-down",
        className,
      )}
    >
      <span aria-hidden>{flat ? "–" : up ? "▲" : "▼"}</span>
      {pct(value)} <span className="text-muted font-normal">{basis}</span>
    </span>
  );
}
