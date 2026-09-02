import { cn } from "@/lib/utils";

// Empty states say WHY they are empty - "no data" and "not yet computed" are different
// problems and must not look identical.
export function EmptyState({ title, message, className }: { title: string; message: string; className?: string }) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-10 text-center", className)}>
      <p className="text-sm font-medium text-secondary">{title}</p>
      <p className="text-xs text-muted mt-1 max-w-sm">{message}</p>
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-md bg-panel-alt", className)} />;
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-center">
      <p className="text-sm font-medium text-price-up">Could not load this data</p>
      <p className="text-xs text-muted mt-1 max-w-sm">{message}</p>
    </div>
  );
}
