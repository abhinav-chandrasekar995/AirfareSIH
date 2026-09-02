"use client";
import { ChartFrame } from "./ChartFrame";
import { seriesColors } from "@/lib/charts/theme";
import { num } from "@/lib/format";

export function SensitivityChart({ points, currentWeight }: {
  points: { weight_pct: number; augmented_index: number; delta: number }[];
  currentWeight: number;
}) {
  const colors = seriesColors();
  const weights = points.map((p) => p.weight_pct);
  const values = points.map((p) => p.augmented_index);

  const option = {
    xAxis: { type: "value", name: "Airfare weight (%)", min: 0 },
    yAxis: { type: "value", scale: true, name: "Augmented index" },
    series: [
      {
        type: "line", data: points.map((p) => [p.weight_pct, p.augmented_index]),
        symbol: "circle", symbolSize: 6, lineStyle: { width: 2, color: colors[0] }, itemStyle: { color: colors[0] },
        markLine: {
          symbol: "none",
          lineStyle: { color: colors[2], type: "dashed" },
          label: { formatter: "current", fontSize: 10 },
          data: [{ xAxis: currentWeight }],
        },
      },
    ],
    tooltip: { trigger: "axis", valueFormatter: (v: number) => num(v, 2) },
  };

  return (
    <ChartFrame
      option={option}
      height={220}
      ariaLabel="Sensitivity of the augmented index to the airfare weight"
      summary={`Augmented index ranges from ${num(Math.min(...values), 2)} to ${num(Math.max(...values), 2)} as the airfare weight varies from ${Math.min(...weights)}% to ${Math.max(...weights)}%.`}
      tableData={{ columns: ["Weight %", "Augmented index", "Delta"], rows: points.map((p) => [p.weight_pct, num(p.augmented_index, 2), num(p.delta, 2)]) }}
    />
  );
}
