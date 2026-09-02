import { cn } from "@/lib/utils";

export function QualityIndicator({ score, band, showBar = true }: { score: number; band: string; showBar?: boolean }) {
  const color = band === "HIGH" ? "bg-quality-high" : band === "MEDIUM" ? "bg-quality-medium" : "bg-quality-low";
  return (
    <span className="inline-flex items-center gap-2" title={`Quality ${score}/100 (${band})`}>
      {showBar && (
        <span className="inline-block h-1.5 w-10 rounded-full bg-panel-alt overflow-hidden" aria-hidden>
          <span className={cn("block h-full rounded-full", color)} style={{ width: `${score}%` }} />
        </span>
      )}
      <span className="numeric text-xs font-medium">{score}</span>
    </span>
  );
}
