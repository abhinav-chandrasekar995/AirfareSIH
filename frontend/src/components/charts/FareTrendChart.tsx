"use client";
import { ChartFrame } from "./ChartFrame";
import { seriesColors } from "@/lib/charts/theme";
import { istDate, inr } from "@/lib/format";
import type { TrendPoint } from "@/types/api";

export function FareTrendChart({ points }: { points: TrendPoint[] }) {
  const dates = points.map((p) => p.date);
  const values = points.map((p) => p.value);
  const colors = seriesColors();

  const option = {
    xAxis: { type: "category", data: dates },
    yAxis: { type: "value", scale: true, axisLabel: { formatter: (v: number) => `₹${(v / 1000).toFixed(1)}k` } },
    series: [
      {
        type: "line",
        data: values,
        symbol: "none",
        lineStyle: { width: 2, color: colors[0] },
        areaStyle: { color: colors[0], opacity: 0.08 },
      },
    ],
    tooltip: { trigger: "axis", valueFormatter: (v: number) => inr(v) },
    dataZoom: [{ type: "inside" }, { type: "slider", height: 16, bottom: 4 }],
  };

  return (
    <ChartFrame
      option={option}
      height={260}
      ariaLabel="Fare trend over time"
      summary={`Median fare ranges from ${inr(Math.min(...values))} to ${inr(Math.max(...values))} across ${points.length} days.`}
      tableData={{ columns: ["Date", "Median fare", "Observations"], rows: points.map((p) => [istDate(p.date), inr(p.value), p.n_observations ?? "—"]) }}
    />
  );
}
