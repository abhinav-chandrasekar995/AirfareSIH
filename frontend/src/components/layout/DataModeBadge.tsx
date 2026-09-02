"use client";
import { cn } from "@/lib/utils";

const MODE_STYLE: Record<string, { dot: string; label: string }> = {
  LIVE: { dot: "bg-mode-live", label: "text-mode-live" },
  CACHED: { dot: "bg-mode-cached", label: "text-mode-cached" },
  REPLAY: { dot: "bg-mode-replay", label: "text-mode-replay" },
};

// Reads the server-provided mode. The UI never presents demo data as live
// (build prompt Sec.33); the badge is derived from meta.data_mode, not a constant.
export function DataModeBadge({ mode, label, description }: { mode: string; label: string; description?: string | null }) {
  const style = MODE_STYLE[mode] ?? MODE_STYLE.REPLAY;
  return (
    <span className="inline-flex items-center gap-1.5 border-[var(--border-hard)] border-border-strong bg-panel px-2.5 py-1 text-[11px] font-mono uppercase tracking-wide" title={description ?? undefined}>
      <span className={cn("h-2 w-2 rounded-full", style.dot)} aria-hidden />
      <span className={cn("font-bold", style.label)}>{label}</span>
    </span>
  );
}
