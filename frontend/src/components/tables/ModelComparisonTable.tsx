import { cn } from "@/lib/utils";
import { num } from "@/lib/format";

interface ModelScore {
  model_name: string;
  validation_mape: number;
  validation_rmse: number;
  selected: boolean;
}

// Model selection is justified by validation error, never asserted (build prompt Sec.17).
export function ModelComparisonTable({ models }: { models: ModelScore[] }) {
  if (models.length === 0) return null;
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="border-b border-border-strong text-left">
          <th className="eyebrow font-semibold py-1.5">Model</th>
          <th className="eyebrow font-semibold py-1.5 text-right">Validation MAPE</th>
          <th className="eyebrow font-semibold py-1.5 text-right">RMSE</th>
          <th className="eyebrow font-semibold py-1.5 text-center">Selected</th>
        </tr>
      </thead>
      <tbody>
        {models.map((m) => (
          <tr key={m.model_name} className={cn("border-b border-border-subtle", m.selected && "bg-panel-alt/60")}>
            <td className="py-1.5">{m.model_name.replace(/_/g, " ")}</td>
            <td className="py-1.5 text-right numeric">{num(m.validation_mape, 2)}%</td>
            <td className="py-1.5 text-right numeric">{num(m.validation_rmse, 1)}</td>
            <td className="py-1.5 text-center">{m.selected ? "✓" : ""}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
