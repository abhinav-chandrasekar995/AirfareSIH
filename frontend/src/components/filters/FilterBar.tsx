import { cn } from "@/lib/utils";

export function FilterBar({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex flex-wrap items-center gap-2 rounded-md border border-border-subtle bg-panel px-3 py-2", className)}>
      {children}
    </div>
  );
}

export function FilterChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <button
      onClick={onRemove}
      className="inline-flex items-center gap-1 rounded-sm bg-panel-alt px-2 py-1 text-[11px] text-secondary hover:bg-border-subtle"
    >
      {label}
      <span aria-hidden>×</span>
    </button>
  );
}
