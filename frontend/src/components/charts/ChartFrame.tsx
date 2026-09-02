"use client";
import { useEffect, useRef, useState } from "react";
import * as echarts from "echarts";
import { Table2 } from "lucide-react";
import { chartBase } from "@/lib/charts/theme";
import { useUiStore } from "@/lib/store/uiStore";

// ChartFrame wraps every ECharts chart with:
//  - a "view as table" toggle (accessible fallback exposing the series to screen readers
//    and to anyone who cannot read the chart) - the ui-ux-pro-max chart a11y rule.
//  - re-theming on light/dark switch.
//  - a required accessible name and text summary.
//
// IMPORTANT: the chart container div is ALWAYS mounted, never conditionally rendered.
// ECharts owns the DOM inside that div (it creates its own canvas/SVG nodes there
// directly, outside React's control). Swapping the div in and out via a ternary - the
// previous version of this component did exactly that - creates a race between React
// unmounting the div and ECharts' own dispose() trying to remove its internal nodes
// from it, which throws "Failed to execute 'removeChild' on 'Node': the node to be
// removed is not a child of this node" and can crash the whole subtree. Visibility is
// toggled with CSS (`hidden`) instead, and the chart instance is created once and kept
// alive across toggles - not disposed and recreated every click.
export function ChartFrame({
  option, height = 260, ariaLabel, summary, tableData,
}: {
  option: echarts.EChartsCoreOption;
  height?: number;
  ariaLabel: string;
  summary: string;
  tableData?: { columns: string[]; rows: (string | number)[][] };
}) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);
  const [showTable, setShowTable] = useState(false);
  const theme = useUiStore((s) => s.theme);

  // Create/update the chart. Depends only on option+theme - NOT on showTable, so
  // toggling the table view never tears down and rebuilds the ECharts instance.
  useEffect(() => {
    if (!ref.current) return;

    let chart = chartRef.current;
    if (!chart || chart.isDisposed()) {
      chart = echarts.init(ref.current, undefined, { renderer: "canvas" });
      chartRef.current = chart;
    }

    const base = chartBase();
    chart.setOption({ ...base, ...option } as echarts.EChartsCoreOption, true);

    const onResize = () => chart?.resize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [option, theme]);

  // Dispose only when the component actually unmounts (empty deps), not on every
  // table/chart toggle.
  useEffect(() => {
    return () => {
      chartRef.current?.dispose();
      chartRef.current = null;
    };
  }, []);

  // A container that was hidden (display:none / zero size) while the table was shown
  // reports stale dimensions to ECharts; resize it once it's visible again.
  useEffect(() => {
    if (!showTable) chartRef.current?.resize();
  }, [showTable]);

  return (
    <figure className="m-0" role="group" aria-label={ariaLabel}>
      <div className="flex items-center justify-end mb-1">
        {tableData && (
          <button
            onClick={() => setShowTable((v) => !v)}
            className="inline-flex items-center gap-1 text-[11px] text-muted hover:text-accent"
            aria-pressed={showTable}
          >
            <Table2 size={12} /> {showTable ? "View chart" : "View as table"}
          </button>
        )}
      </div>
      <p className="sr-only">{summary}</p>

      <div ref={ref} style={{ height, width: "100%" }} hidden={showTable} aria-hidden={showTable} />

      {tableData && (
        <div className="overflow-x-auto" style={{ maxHeight: height + 20 }} hidden={!showTable}>
          <table className="w-full text-xs numeric">
            <thead className="sticky top-0 bg-panel">
              <tr className="border-b border-border-strong text-left">
                {tableData.columns.map((c) => (
                  <th key={c} className="px-2 py-1 eyebrow font-semibold">{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableData.rows.map((row, i) => (
                <tr key={i} className="border-b border-border-subtle">
                  {row.map((cell, j) => (
                    <td key={j} className="px-2 py-1">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </figure>
  );
}
