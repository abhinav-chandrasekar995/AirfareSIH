"use client";
import { ChartFrame } from "./ChartFrame";
import { seriesColors } from "@/lib/charts/theme";
import { istDate, num } from "@/lib/format";
import type { ApixPoint } from "@/types/api";

// Reference lines against the index's own base=100 convention. These are level-vs-base
// guides, not the WoW alert thresholds used by /apix/alert.
const RBI_LOWER_BAND_PCT = 4.0;
const RBI_UPPER_BAND_PCT = 6.0;

export function ApixTrendChart({ points, mode }: { points: ApixPoint[]; mode: "core" | "headline" }) {
  const colors = seriesColors();
  const dates = points.map((p) => p.date);
  const values = points.map((p) => p.index_value);
  const lowerBand = 100 * (1 + RBI_LOWER_BAND_PCT / 100);
  const upperBand = 100 * (1 + RBI_UPPER_BAND_PCT / 100);
  const label = mode === "core" ? "Core APIx (base fare)" : "Headline APIx (total fare)";

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
        markLine: {
          symbol: "none",
          label: { formatter: "{b}", fontSize: 10, position: "insideEndTop" },
          lineStyle: { type: "dashed", width: 1.5 },
          data: [
            { yAxis: lowerBand, name: `Base level +${RBI_LOWER_BAND_PCT.toFixed(1)}%`, lineStyle: { color: "var(--warn-600)" } },
            { yAxis: upperBand, name: `Base level +${RBI_UPPER_BAND_PCT.toFixed(1)}%`, lineStyle: { color: "var(--signal-600)" } },
          ],
        },
      },
    ],
    tooltip: { trigger: "axis", valueFormatter: (v: number) => num(v, 2) },
    dataZoom: [{ type: "inside" }, { type: "slider", height: 16, bottom: 4 }],
  };

  return (
    <ChartFrame
      option={option}
      height={300}
      ariaLabel={`${label} trend over time, with base-level references at plus ${RBI_LOWER_BAND_PCT}% and ${RBI_UPPER_BAND_PCT}%`}
      summary={`${label} ranges from ${num(Math.min(...values), 1)} to ${num(Math.max(...values), 1)} across ${points.length} days, against base-level references at ${num(lowerBand, 1)} and ${num(upperBand, 1)} (base=100).`}
      tableData={{
        columns: ["Date", label],
        rows: points.map((p) => [istDate(p.date), num(p.index_value, 2)]),
      }}
    />
  );
}
