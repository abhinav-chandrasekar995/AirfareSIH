"use client";
import { ChartFrame } from "./ChartFrame";
import { seriesColors } from "@/lib/charts/theme";
import { num } from "@/lib/format";
import type { MospiComparisonPoint } from "@/types/api";

// Official (solid blue) stops naturally where MoSPI's real data stops - ECharts breaks
// a line series on `null`, so no fake "official" value is ever drawn past that point.
// Nowcast (dashed red) runs the full range; the markArea after the last official month
// is the "Data Lag Gap" - the honest, real gap between what MoSPI has published and
// what we already know. See app/services/mospi_service.py.
export function MospiComparisonChart({
  points, lastOfficialMonth, dataLagDays,
}: {
  points: MospiComparisonPoint[];
  lastOfficialMonth: string;
  dataLagDays: number;
}) {
  const colors = seriesColors();
  const months = points.map((p) => p.month.slice(0, 7));
  const official = points.map((p) => p.official_index);
  const nowcast = points.map((p) => p.nowcast_index);
  const gapStartIdx = points.findIndex((p) => p.month > lastOfficialMonth);

  const option: any = {
    xAxis: { type: "category", data: months },
    yAxis: { type: "value", scale: true, name: "Airfare CPI / rebased APIx", nameTextStyle: { fontSize: 10 } },
    legend: { top: 0, right: 0, textStyle: { fontSize: 11 } },
    series: [
      {
        name: "Official (e-Sankhyiki)",
        type: "line",
        data: official,
        connectNulls: false,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: { width: 2.5, color: colors[0] },
        itemStyle: { color: colors[0] },
      },
      {
        name: "Nowcasted APIx (rebased)",
        type: "line",
        data: nowcast,
        symbol: "diamond",
        symbolSize: 5,
        lineStyle: { width: 2, type: "dashed", color: colors[2] },
        itemStyle: { color: colors[2] },
        markArea:
          gapStartIdx >= 0
            ? {
                itemStyle: { color: colors[2], opacity: 0.07 },
                label: { formatter: `Data Lag Gap\n+${dataLagDays}d ahead of e-Sankhyiki`, fontSize: 10, position: "insideTop" },
                data: [[{ xAxis: months[gapStartIdx] }, { xAxis: months[months.length - 1] }]],
              }
            : undefined,
      },
    ],
    tooltip: { trigger: "axis", valueFormatter: (v: number) => (v === null ? "not yet released" : num(v, 2)) },
  };

  return (
    <ChartFrame
      option={option}
      height={300}
      ariaLabel="Official MoSPI Airfare CPI compared to our rebased nowcasted APIx, with the data lag gap highlighted"
      summary={`Official MoSPI Airfare CPI is available through ${lastOfficialMonth.slice(0, 7)}. Our rebased nowcasted APIx continues ${dataLagDays} days beyond that, into months MoSPI has not yet released.`}
      tableData={{
        columns: ["Month", "Official (MoSPI)", "Nowcasted APIx (rebased)"],
        rows: points.map((p) => [p.month.slice(0, 7), p.official_index !== null ? num(p.official_index, 2) : "not yet released", num(p.nowcast_index, 2)]),
      }}
    />
  );
}
