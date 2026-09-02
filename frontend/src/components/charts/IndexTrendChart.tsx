"use client";
import { ChartFrame } from "./ChartFrame";
import { seriesColors } from "@/lib/charts/theme";
import { istDate, num } from "@/lib/format";
import type { IndexPoint } from "@/types/api";

// National/regional/route index trend. Y-axis is NOT forced to zero (design doc §4.7) -
// forcing zero on an index series destroys the resolution that makes movement visible.
export function IndexTrendChart({ points, label = "Index" }: { points: IndexPoint[]; label?: string }) {
  const dates = points.map((p) => p.date);
  const values = points.map((p) => p.index_value);
  const colors = seriesColors();

  const option = {
    xAxis: { type: "category", data: dates },
    yAxis: { type: "value", scale: true, name: label, nameTextStyle: { fontSize: 10 } },
    series: [
      {
        type: "line",
        data: values,
        smooth: false,
        symbol: "none",
        lineStyle: { width: 2, color: colors[0] },
        areaStyle: { color: colors[0], opacity: 0.08 },
      },
    ],
    tooltip: {
      trigger: "axis",
      valueFormatter: (v: number) => num(v, 2),
    },
    dataZoom: [{ type: "inside" }, { type: "slider", height: 16, bottom: 4 }],
  };

  return (
    <ChartFrame
      option={option}
      height={280}
      ariaLabel={`${label} trend over time`}
      summary={`${label} ranges from ${num(Math.min(...values), 1)} to ${num(Math.max(...values), 1)} across ${points.length} periods.`}
      tableData={{
        columns: ["Date", label],
        rows: points.map((p) => [istDate(p.date), num(p.index_value, 2)]),
      }}
    />
  );
}
