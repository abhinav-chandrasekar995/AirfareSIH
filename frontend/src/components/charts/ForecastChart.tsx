"use client";
import { ChartFrame } from "./ChartFrame";
import { seriesColors } from "@/lib/charts/theme";
import { istDate, num } from "@/lib/format";
import type { ForecastPoint } from "@/types/api";

// A point forecast must never render alone (build prompt Sec.17). `points` here always
// carry lower/upper bounds from the backend schema (ForecastPoint requires them), so
// there is no code path in this component that can plot a bare prediction.
export function ForecastChart({ points }: { points: ForecastPoint[] }) {
  const dates = points.map((p) => istDate(p.forecast_date));
  const colors = seriesColors();

  // Band drawn as a filled area between lower and upper bounds.
  const lower = points.map((p) => p.lower_bound);
  const bandHeight = points.map((p) => p.upper_bound - p.lower_bound);
  const prediction = points.map((p) => p.prediction);

  const option = {
    xAxis: { type: "category", data: dates },
    yAxis: { type: "value", scale: true, name: "APIx index", nameTextStyle: { fontSize: 10 }, axisLabel: { formatter: (v: number) => num(v, 0) } },
    series: [
      { name: "Lower bound", type: "line", data: lower, symbol: "none", lineStyle: { opacity: 0 }, stack: "band" },
      {
        name: "Confidence interval", type: "line", data: bandHeight, symbol: "none",
        lineStyle: { opacity: 0 }, areaStyle: { color: colors[0], opacity: 0.15 }, stack: "band",
      },
      {
        name: "Forecast", type: "line", data: prediction, symbol: "circle", symbolSize: 5,
        lineStyle: { width: 2, type: "dashed", color: colors[0] }, itemStyle: { color: colors[0] },
      },
    ],
    tooltip: {
      trigger: "axis",
      formatter: (params: any[]) => {
        const p = points[params[0]?.dataIndex ?? 0];
        if (!p) return "";
        return `${istDate(p.forecast_date)}<br/>Prediction: ${num(p.prediction, 2)} APIx<br/>Range: ${num(p.lower_bound, 2)} – ${num(p.upper_bound, 2)}`;
      },
    },
  };

  return (
    <ChartFrame
      option={option}
      height={280}
      ariaLabel="Forecast with prediction interval"
      summary={`Forecast over ${points.length} days, prediction interval width from ${num(Math.min(...bandHeight), 2)} to ${num(Math.max(...bandHeight), 2)} APIx points.`}
      tableData={{
        columns: ["Date", "Prediction", "Lower", "Upper"],
        rows: points.map((p) => [istDate(p.forecast_date), num(p.prediction, 2), num(p.lower_bound, 2), num(p.upper_bound, 2)]),
      }}
    />
  );
}
