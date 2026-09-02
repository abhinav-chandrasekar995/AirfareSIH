import { AlertTriangle } from "lucide-react";

// Persistent, non-dismissible disclaimer (build prompt Sec.15). No prop to hide it,
// no local dismissed-state - it cannot be closed by construction.
export function DisclaimerBanner({ text }: { text: string }) {
  return (
    <div
      role="alert"
      className="flex items-start gap-2.5 rounded-md border border-[var(--warn-400)] bg-[var(--warn-100)] px-4 py-3 text-[var(--warn-700)] mb-4"
    >
      <AlertTriangle size={16} className="mt-0.5 shrink-0" aria-hidden />
      <p className="text-xs font-medium leading-relaxed">
        <strong className="uppercase tracking-wide mr-1">Simulation only.</strong>
        {text}
      </p>
    </div>
  );
}
