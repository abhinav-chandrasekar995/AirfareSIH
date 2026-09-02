"use client";
import { ChartFrame } from "./ChartFrame";
import { seriesColors } from "@/lib/charts/theme";
import { num } from "@/lib/format";

// Our index vs the DGCA benchmark. Distinguished by line STYLE (solid vs dashed) as
// well as colour - the ui-ux-pro-max chart rule: never rely on hue alone.
export function BenchmarkOverlayChart({ series, splitIndex }: {
  series: { month: string; ours: number; dgca: number }[];
  splitIndex?: number;
}) {
  const colors = seriesColors();
  const months = series.map((s) => s.month.slice(0, 7));

  const option: any = {
    xAxis: { type: "category", data: months },
    yAxis: { type: "value", scale: true, name: "Index" },
    legend: { top: 0, right: 0, textStyle: { fontSize: 11 } },
    series: [
      { name: "Our index", type: "line", data: series.map((s) => s.ours), symbol: "circle", symbolSize: 5, lineStyle: { width: 2, color: colors[0] }, itemStyle: { color: colors[0] } },
      { name: "DGCA benchmark", type: "line", data: series.map((s) => s.dgca), symbol: "diamond", symbolSize: 5, lineStyle: { width: 2, type: "dashed", color: colors[2] }, itemStyle: { color: colors[2] } },
    ],
    tooltip: { trigger: "axis" },
  };

  if (splitIndex !== undefined && splitIndex >= 0 && splitIndex < months.length) {
    option.series[0].markLine = {
      symbol: "none",
      label: { formatter: "Train | Test", fontSize: 10 },
      lineStyle: { color: "var(--text-muted)", type: "dotted" },
      data: [{ xAxis: months[splitIndex] }],
    };
  }

  return (
    <ChartFrame
      option={option}
      height={280}
      ariaLabel="Our index compared to the DGCA benchmark"
      summary={`Comparison across ${series.length} months between our computed index and the DGCA benchmark series.`}
      tableData={{ columns: ["Month", "Our index", "DGCA benchmark"], rows: series.map((s) => [s.month.slice(0, 7), num(s.ours, 2), num(s.dgca, 2)]) }}
    />
  );
}
