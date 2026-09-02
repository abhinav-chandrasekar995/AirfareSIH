"use client";
import { ChartFrame } from "./ChartFrame";
import { seriesColors } from "@/lib/charts/theme";
import { inr } from "@/lib/format";
import type { LeadTimePoint } from "@/types/api";

export function LeadTimeCurveChart({ points }: { points: LeadTimePoint[] }) {
  const labels = points.map((p) => `T+${p.lead_days}`);
  const values = points.map((p) => p.avg_fare);
  const colors = seriesColors();

  const option = {
    xAxis: { type: "category", data: labels, name: "Booking window" },
    yAxis: { type: "value", scale: true, axisLabel: { formatter: (v: number) => `₹${(v / 1000).toFixed(1)}k` } },
    series: [
      {
        type: "line",
        data: values,
        symbol: "circle",
        symbolSize: 7,
        lineStyle: { width: 2.5, color: colors[2] },
        itemStyle: { color: colors[2] },
        areaStyle: { color: colors[2], opacity: 0.06 },
      },
    ],
    tooltip: { trigger: "axis", valueFormatter: (v: number) => inr(v) },
  };

  return (
    <ChartFrame
      option={option}
      height={260}
      ariaLabel="Fare by booking window (lead-time curve)"
      summary={`Fares range from ${inr(Math.min(...values))} at the earliest booking window to ${inr(Math.max(...values))} at the latest.`}
      tableData={{
        columns: ["Window", "Avg fare", "Observations", "vs earliest"],
        rows: points.map((p) => [`T+${p.lead_days}`, inr(p.avg_fare), p.n_observations, p.vs_earliest_pct !== null ? `${p.vs_earliest_pct > 0 ? "+" : ""}${p.vs_earliest_pct}%` : "—"]),
      }}
    />
  );
}
