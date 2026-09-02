import { cn } from "@/lib/utils";
import { inr } from "@/lib/format";

const COMPONENTS: { key: string; label: string; color: string }[] = [
  { key: "base_fare", label: "Base fare", color: "var(--series-1)" },
  { key: "taxes", label: "Taxes", color: "var(--series-3)" },
  { key: "udf", label: "UDF", color: "var(--series-5)" },
  { key: "airport_charges", label: "Airport charges", color: "var(--series-4)" },
  { key: "convenience_fee", label: "Convenience fee", color: "var(--series-8)" },
];

// Fare composition: Base + Taxes + UDF + Airport charges + Convenience fee = Total.
// Renders both the stacked visual and the table, so the reconciliation is checkable.
export function FareCompositionBar({ composition }: { composition: Record<string, number> }) {
  const total = composition.total_fare || 1;
  const reconciles = composition.reconciles !== 0;

  return (
    <div>
      <div className="flex h-6 w-full rounded-sm overflow-hidden border border-border-subtle" role="img" aria-label="Fare composition breakdown">
        {COMPONENTS.map((c) => {
          const value = composition[c.key] || 0;
          const width = (value / total) * 100;
          return width > 0 ? (
            <div key={c.key} style={{ width: `${width}%`, background: c.color }} title={`${c.label}: ${inr(value)}`} />
          ) : null;
        })}
      </div>
      <table className="w-full text-xs mt-3 numeric">
        <tbody>
          {COMPONENTS.map((c) => (
            <tr key={c.key} className="border-b border-border-subtle">
              <td className="py-1 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full inline-block" style={{ background: c.color }} />
                {c.label}
              </td>
              <td className="py-1 text-right">{inr(composition[c.key])}</td>
              <td className="py-1 text-right text-muted w-12">{composition[`${c.key}_pct`]?.toFixed(1)}%</td>
            </tr>
          ))}
          <tr className="font-semibold">
            <td className="py-1.5">Total consumer fare</td>
            <td className="py-1.5 text-right">{inr(composition.total_fare)}</td>
            <td className="py-1.5 text-right">100%</td>
          </tr>
        </tbody>
      </table>
      <p className={cn("text-[11px] mt-1", reconciles ? "text-muted" : "text-price-up")}>
        {reconciles ? "Components reconcile to the recorded total." : "Components do not fully reconcile — flagged by the tax-consistency quality check."}
      </p>
    </div>
  );
}
