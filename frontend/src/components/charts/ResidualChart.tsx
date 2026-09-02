"use client";
import { ChartFrame } from "./ChartFrame";
import { seriesColors } from "@/lib/charts/theme";
import { num } from "@/lib/format";

export function ResidualChart({ series }: { series: { month: string; ours: number; dgca: number }[] }) {
  const colors = seriesColors();
  const months = series.map((s) => s.month.slice(0, 7));
  const residuals = series.map((s) => Number((s.ours - s.dgca).toFixed(2)));

  const option = {
    xAxis: { type: "category", data: months },
    yAxis: { type: "value", name: "Residual" },
    series: [
      {
        type: "bar",
        data: residuals.map((r) => ({ value: r, itemStyle: { color: r >= 0 ? colors[5] : colors[1] } })),
        barMaxWidth: 24,
      },
    ],
    tooltip: { trigger: "axis", valueFormatter: (v: number) => num(v, 2) },
  };

  return (
    <ChartFrame
      option={option}
      height={180}
      ariaLabel="Residual error between our index and the DGCA benchmark"
      summary={`Residuals range from ${num(Math.min(...residuals), 2)} to ${num(Math.max(...residuals), 2)} across ${series.length} months.`}
      tableData={{ columns: ["Month", "Residual"], rows: months.map((m, i) => [m, num(residuals[i], 2)]) }}
    />
  );
}
