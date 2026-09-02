// ECharts theme derived from the design tokens at runtime, so charts and UI share one
// palette and recolour together on theme switch. Colours are read from CSS variables
// rather than hardcoded (design doc §10).

function cssVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

export function seriesColors(): string[] {
  return [
    cssVar("--series-1", "#3B4FD8"),
    cssVar("--series-2", "#0E8B4F"),
    cssVar("--series-3", "#C4870F"),
    cssVar("--series-4", "#6D4AE0"),
    cssVar("--series-5", "#0F7490"),
    cssVar("--series-6", "#C82333"),
    cssVar("--series-7", "#7A5C3E"),
    cssVar("--series-8", "#5E6773"),
  ];
}

export function chartBase() {
  const text = cssVar("--text-muted", "#6B7480");
  const grid = cssVar("--border-subtle", "#E1E5EB");
  const strong = cssVar("--border-strong", "#0A0E1A");
  const panel = cssVar("--bg-panel", "#FFFFFF");
  const primary = cssVar("--text-primary", "#070B18");
  const signal = cssVar("--signal-600", "#FF3B1F");

  return {
    textStyle: { fontFamily: "Fira Sans, sans-serif", color: text },
    grid: { left: 52, right: 20, top: 28, bottom: 36, containLabel: true },
    // Horizontal grid only; no vertical noise (design doc §4.7). Axis line uses the
    // hard "border-strong" token so charts carry the same raw-edge language as the
    // panels around them, without touching data density or legibility.
    xAxis: {
      axisLine: { lineStyle: { color: strong, width: 2 } },
      axisTick: { show: false },
      axisLabel: { color: text, fontSize: 11, fontFamily: "Fira Code, monospace" },
      splitLine: { show: false },
    },
    yAxis: {
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: text, fontSize: 11, fontFamily: "Fira Code, monospace" },
      splitLine: { lineStyle: { color: grid, type: "solid" } },
    },
    tooltip: {
      backgroundColor: cssVar("--navy-850", "#101828"),
      borderColor: strong,
      borderWidth: 2,
      borderRadius: 0,
      textStyle: { color: cssVar("--navy-100", "#E4EAF4"), fontFamily: "Fira Sans" },
      axisPointer: { lineStyle: { color: signal, width: 1.5 } },
    },
    _panel: panel,
    _primary: primary,
    _grid: grid,
  };
}

// Line-style cycle so multi-series charts are distinguishable without relying on hue
// alone (ui-ux-pro-max chart accessibility rule).
export const LINE_STYLES = ["solid", "dashed", "dotted"] as const;
