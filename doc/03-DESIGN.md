# Design Document
## INDIA AIRFARE INTELLIGENCE

| Field | Value |
|---|---|
| Document | UI/UX & Visual Design Specification |
| Version | 1.0 |
| Implementation | Next.js + React + TypeScript + Tailwind CSS + shadcn/ui + ECharts/Plotly |
| Last updated | 2026-09-01 |
| Related docs | [PRD](01-PRD.md) · [Architecture](02-ARCHITECTURE.md) · [Schema](04-BACKEND-SCHEMA.md) · [Folder Structure](05-FOLDER-STRUCTURE.md) |

---

## 1. Design thesis

> This product must feel like a **statistical instrument**, not a travel website.

The visual reference set is **Bloomberg Terminal, RBI/NSO statistical portals, and modern analytics SaaS**. The anti-reference set is **MakeMyTrip, Skyscanner, and generic AI-dashboard templates**.

### 1.1 The five-second test

A judge who sees the screen for five seconds with no explanation should conclude: *"this is a government-grade measurement system."* If their first instinct is *"can I book a flight here?"*, the design has failed.

### 1.2 Design principles

| # | Principle | What it means in practice |
|---|---|---|
| D1 | **Density is credibility** | Financial analysts trust dense screens. Do not pad. Show more real numbers per viewport than a consumer product would. |
| D2 | **Every number is sourced** | Any displayed figure has a visible provenance path: hover for method, click to drill into inputs. |
| D3 | **Uncertainty is shown, never hidden** | Forecasts render with intervals. Low-quality data renders with a quality badge. Estimates are labelled as estimates. |
| D4 | **Colour carries meaning only** | Colour encodes direction (up/down), severity, and quality. Never decoration. |
| D5 | **Charts over chrome** | Budget for chart area; spend nothing on gradients, glassmorphism, or illustration. |
| D6 | **Serious, not sterile** | Restraint and precision, not a grey wall. Accent colour and typographic hierarchy carry the interest. |
| D7 | **Honest state** | Cached, replayed and simulated data are visibly labelled at all times. |

---

## 2. Design tokens

### 2.1 Colour — primitive layer

The palette is a deep-navy statistical base with a single analytical accent and a strict semantic set.

```css
/* ---------- Neutrals: navy-slate scale ---------- */
--navy-950:  #070B18;   /* app background, dark mode          */
--navy-900:  #0B1120;   /* panel background, dark mode        */
--navy-850:  #101828;   /* elevated surface                   */
--navy-800:  #16203A;   /* borders on dark, hover fills       */
--navy-700:  #1F2C4C;
--navy-600:  #2C3D63;
--navy-500:  #405582;
--navy-400:  #6B80AB;   /* muted text on dark                 */
--navy-300:  #9AACCB;
--navy-200:  #C6D2E6;
--navy-100:  #E4EAF4;
--navy-50:   #F4F7FC;   /* app background, light mode         */
--white:     #FFFFFF;

/* ---------- Cool grey (tables, rules, axes) ---------- */
--grey-900:  #14181F;
--grey-700:  #333B49;
--grey-500:  #6B7480;
--grey-400:  #939BA7;
--grey-300:  #C3C9D2;
--grey-200:  #E1E5EB;
--grey-100:  #F1F3F7;

/* ---------- Analytical accent ---------- */
--accent-700: #2C3FB8;
--accent-600: #3B4FD8;   /* primary interactive               */
--accent-500: #5468F0;
--accent-400: #7C8BF5;
--accent-300: #A9B3F9;
--accent-100: #E5E8FE;

--violet-600: #6D4AE0;   /* secondary analytical series       */
--violet-400: #9B84EF;

/* ---------- Semantic: market direction ---------- */
--up-700:     #0B6E3F;
--up-600:     #0E8B4F;   /* price increase / positive move    */
--up-400:     #35B677;
--up-100:     #E3F5EC;

--down-700:   #A11C2B;
--down-600:   #C82333;   /* price decrease / abnormal pressure*/
--down-400:   #E2596A;
--down-100:   #FDE9EB;

--warn-700:   #96650B;
--warn-600:   #C4870F;   /* warning / medium severity         */
--warn-400:   #E0AB4A;
--warn-100:   #FDF3E0;

--info-600:   #0F7490;
--info-100:   #E2F3F8;
```

> **Direction convention.** In this product, **green = price increase** and **red = price decrease** is *wrong*. For a consumer-price index, a rising price is the adverse condition. We therefore use: **red/amber = upward price pressure (adverse)**, **green = downward price movement (benign)**. This is stated explicitly in a legend on the dashboard so it can never be misread, and it matches how inflation dashboards at statistical agencies present the same information.

### 2.2 Colour — semantic layer

```css
:root {
  /* Surfaces */
  --bg-app:            var(--navy-50);
  --bg-panel:          var(--white);
  --bg-panel-alt:      var(--grey-100);
  --bg-elevated:       var(--white);
  --bg-inset:          var(--navy-50);

  /* Text */
  --text-primary:      var(--navy-950);
  --text-secondary:    var(--grey-700);
  --text-muted:        var(--grey-500);
  --text-inverse:      var(--white);
  --text-accent:       var(--accent-600);

  /* Lines */
  --border-subtle:     var(--grey-200);
  --border-strong:     var(--grey-300);
  --border-focus:      var(--accent-600);

  /* Interactive */
  --interactive-primary:        var(--accent-600);
  --interactive-primary-hover:  var(--accent-700);

  /* Market semantics (see direction convention above) */
  --price-up:          var(--down-600);   /* adverse: fares rising  */
  --price-up-bg:       var(--down-100);
  --price-down:        var(--up-600);     /* benign: fares falling  */
  --price-down-bg:     var(--up-100);
  --price-flat:        var(--grey-500);

  /* Severity */
  --sev-critical:      var(--down-700);
  --sev-high:          var(--down-600);
  --sev-medium:        var(--warn-600);
  --sev-low:           var(--info-600);

  /* Data quality */
  --quality-high:      var(--up-600);
  --quality-medium:    var(--warn-600);
  --quality-low:       var(--down-600);

  /* Data mode badge */
  --mode-live:         var(--up-600);
  --mode-cached:       var(--warn-600);
  --mode-replay:       var(--violet-600);
}

:root[data-theme="dark"] {
  --bg-app:            var(--navy-950);
  --bg-panel:          var(--navy-900);
  --bg-panel-alt:      var(--navy-850);
  --bg-elevated:       var(--navy-850);
  --bg-inset:          var(--navy-950);

  --text-primary:      var(--navy-100);
  --text-secondary:    var(--navy-300);
  --text-muted:        var(--navy-400);
  --text-accent:       var(--accent-400);

  --border-subtle:     var(--navy-800);
  --border-strong:     var(--navy-700);

  --price-up:          var(--down-400);
  --price-up-bg:       rgba(200, 35, 51, 0.16);
  --price-down:        var(--up-400);
  --price-down-bg:     rgba(14, 139, 79, 0.16);
}
```

**Dark mode is the default** for the analyst-facing app. It reads as a terminal, reduces chart glare, and separates the product visually from consumer travel sites. Light mode exists for projection and printed reports, where dark backgrounds fail.

### 2.3 Categorical series palette (charts)

Ordered, colour-blind-safe, tested against both themes:

```css
--series-1: #3B4FD8;   /* accent blue      */
--series-2: #0E8B4F;   /* green            */
--series-3: #C4870F;   /* amber            */
--series-4: #6D4AE0;   /* violet           */
--series-5: #0F7490;   /* teal             */
--series-6: #C82333;   /* red              */
--series-7: #7A5C3E;   /* brown            */
--series-8: #5E6773;   /* slate            */
```

**Fixed assignments** (a carrier keeps the same colour on every screen, so comparison across pages is instant):

| Entity | Series slot |
|---|---|
| IndiGo | `--series-1` |
| Air India | `--series-6` |
| Air India Express | `--series-3` |
| Akasa Air | `--series-4` |
| SpiceJet | `--series-5` |
| Airline Direct (source) | `--series-8` |
| Our index (vs benchmark) | `--series-1` |
| DGCA benchmark | `--series-3`, dashed |

Sequential ramp for the pressure map (low -> high price pressure):

```css
--ramp-0: #E4EAF4;  --ramp-1: #FDF3E0;  --ramp-2: #F7D9A8;
--ramp-3: #EFA96B;  --ramp-4: #E2596A;  --ramp-5: #A11C2B;
```

### 2.4 Typography

```css
--font-sans:  "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
--font-mono:  "JetBrains Mono", "SF Mono", "Consolas", monospace;
--font-display: "Inter Tight", "Inter", system-ui, sans-serif;
```

**All numerals are tabular.** Non-tabular figures in a financial table are a correctness problem, not a taste problem — columns must align for scanning.

```css
.numeric { font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1; }
```

Type scale:

| Token | Size / line-height | Weight | Usage |
|---|---|---|---|
| `--text-hero` | 56px / 1.05 | 700, display, tabular | The India Airfare Index headline number |
| `--text-kpi` | 34px / 1.15 | 650, tabular | KPI card values |
| `--text-h1` | 26px / 1.25 | 640 | Page titles |
| `--text-h2` | 20px / 1.3 | 620 | Section headers |
| `--text-h3` | 16px / 1.4 | 600 | Panel titles |
| `--text-body` | 14px / 1.55 | 400 | Default body |
| `--text-sm` | 13px / 1.5 | 400 | Table cells, secondary |
| `--text-xs` | 11.5px / 1.45 | 500 | Labels, axis ticks, badges |
| `--text-micro` | 10.5px / 1.4 | 600, uppercase, 0.06em tracking | Card eyebrow labels, table headers |
| `--text-mono` | 13px / 1.5 | 400, mono | Codes (DEL-BOM, 6E-2134), API examples, IDs |

### 2.5 Spacing, radius, elevation

```css
/* 4px base grid */
--space-1: 4px;   --space-2: 8px;   --space-3: 12px;  --space-4: 16px;
--space-5: 20px;  --space-6: 24px;  --space-8: 32px;  --space-10: 40px;
--space-12: 48px; --space-16: 64px;

/* Restrained radii - sharp reads as instrument, round reads as consumer app */
--radius-sm: 4px;    /* badges, inputs        */
--radius-md: 6px;    /* buttons, cards        */
--radius-lg: 8px;    /* panels, modals        */
--radius-full: 999px;/* status dots only      */

/* Elevation: borders do most of the work; shadows are subtle */
--shadow-sm: 0 1px 2px rgba(7, 11, 24, 0.06);
--shadow-md: 0 2px 8px rgba(7, 11, 24, 0.08);
--shadow-lg: 0 8px 24px rgba(7, 11, 24, 0.12);
--shadow-none: none;   /* dark mode panels use borders, not shadows */
```

### 2.6 Motion

```css
--ease-out:  cubic-bezier(0.16, 1, 0.3, 1);
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
--dur-fast:   120ms;   /* hover, focus            */
--dur-base:   200ms;   /* panel/tab transitions   */
--dur-slow:   400ms;   /* chart series draw-in    */
```

Motion rules: charts animate **once** on mount, never on every data refresh (a re-animating chart during a demo reads as instability). No parallax, no scroll-jacking, no decorative animation. `prefers-reduced-motion: reduce` disables all non-essential transitions.

---

## 3. Layout system

### 3.1 App shell

```
+------------------------------------------------------------------------------+
| TOP BAR  h=56                                                                |
| [logo] INDIA AIRFARE INTELLIGENCE   |  [LIVE .] Updated 04:12 IST  [search]  |
|                                     |  [theme] [key] [profile]               |
+---------------+--------------------------------------------------------------+
|               |                                                              |
| SIDEBAR       |  PAGE HEADER   title + subtitle + global filters             |
| w=232         |  ----------------------------------------------------------- |
| (collapse 64) |                                                              |
|               |  CONTENT GRID  12 columns, 20px gutter, max-width 1680px     |
| Dashboard     |                                                              |
| Airfare Index |  +-------------------+  +-------------------+                |
| Route Intel   |  |                   |  |                   |                |
| Anomaly Intel |  |      PANEL        |  |      PANEL        |                |
| Lead-Time     |  |                   |  |                   |                |
| CPI Simulator |  +-------------------+  +-------------------+                |
| Backtest/Fcst |                                                              |
| Data Explorer |  +--------------------------------------------------+        |
| Collection    |  |                    PANEL                          |       |
| API Portal    |  +--------------------------------------------------+        |
| Reports       |                                                              |
| Settings      |                                                              |
+---------------+--------------------------------------------------------------+
```

### 3.2 Grid and breakpoints

| Breakpoint | Width | Grid | Sidebar |
|---|---|---|---|
| `xs` | < 640px | 4 col, stacked | Off-canvas drawer |
| `sm` | 640-1023 | 6 col | Off-canvas |
| `md` | 1024-1279 | 8 col | Icon rail (64px) |
| `lg` | 1280-1535 | 12 col | Expanded (232px) |
| `xl` | 1536+ | 12 col, max 1680px | Expanded |

The product is **desktop-first** — its users are analysts on large screens, and judging happens on a projector. Mobile is supported (readable, navigable) but not optimised for; dense tables become card lists below `md`.

### 3.3 Panel anatomy

Every analytical panel uses one structure, which is what gives the product its coherence:

```
+----------------------------------------------------------+
| TITLE                          [range] [export] [info(i)] |  <- header 40px
| Optional one-line subtitle / method note                  |
+----------------------------------------------------------+
|                                                          |
|                    CONTENT                               |
|              (chart / table / stats)                     |
|                                                          |
+----------------------------------------------------------+
| Source: IndiGo, MMT  ·  n=1,284  ·  quality>=60           |  <- footer 28px
+----------------------------------------------------------+
```

The **footer strip is mandatory** on every data panel. It shows source attribution, observation count, and the quality threshold applied. This single component is what operationalises principle D2 (every number is sourced) and it is the detail that most distinguishes this product from a dashboard template.

---

## 4. Component specifications

### 4.1 KPI card

```
+---------------------------------+
| INDIA AIRFARE INDEX         (i) |   micro label, uppercase, --text-muted
|                                 |
| 127.4                           |   --text-kpi, tabular, --text-primary
|                                 |
| ^ 7.4%  MoM      base 2025=100  |   delta chip + context, --text-xs
+---------------------------------+
```

- Value uses tabular numerals; the delta chip is `--price-up-bg` / `--price-up` when fares rose.
- Arrow glyphs are triangles, not emoji.
- `(i)` opens a popover: what this measures, how it is computed, methodology version link.
- Entire card is a link to the module that computes it (FR-M1-2 traceability).
- Skeleton state matches final layout dimensions exactly to prevent layout shift.

**Hero variant** (dashboard, index page): the national index renders at `--text-hero` with a sparkline of the last 30 days beneath, spanning 4 grid columns.

### 4.2 Delta chip

| State | Background | Text | Glyph |
|---|---|---|---|
| Fares up (adverse) | `--price-up-bg` | `--price-up` | filled up triangle |
| Fares down (benign) | `--price-down-bg` | `--price-down` | filled down triangle |
| Flat (< 0.5%) | `--bg-panel-alt` | `--price-flat` | en dash |

Always `+`/`-` signed, always one decimal place, always with the comparison basis (`MoM`, `WoW`, `YoY`) adjacent.

### 4.3 Severity badge

```
CRITICAL   solid --sev-critical, white text
HIGH       solid --sev-high, white text
MEDIUM     tinted --warn-100 bg, --warn-700 text, 1px --warn-400 border
LOW        tinted --info-100 bg, --info-600 text
```

Uppercase, `--text-micro`, `--radius-sm`, 4px vertical / 8px horizontal padding. Severity is also encoded by a 3px left border on the anomaly row, so severity survives greyscale printing and colour-blind viewing.

### 4.4 Quality score indicator

```
 [====----]  94   HIGH CONFIDENCE
```

A 40px micro-bar plus the numeric score plus the band label. Colour from `--quality-*`. Appears in the Data Explorer table, on observation detail, and in panel footers as an aggregate.

### 4.5 Data mode badge (top bar, always visible)

```
[ • LIVE ]     green dot, "Updated 04:12 IST"
[ • CACHED ]   amber dot, "Cached data - last collection 11h ago"
[ • REPLAY ]   violet dot, "Replayed dataset for demonstration"
```

Reads `meta.data_mode` from the API. Non-dismissible. This is the honest-state principle (D7) made concrete, and it is what lets the demo run offline without misleading anyone.

### 4.6 Data table

- Sticky header, `--text-micro` uppercase labels, `--border-strong` bottom rule.
- Row height 36px (compact) / 44px (comfortable), user-toggleable.
- Numeric columns right-aligned and tabular; text columns left-aligned; codes in `--font-mono`.
- Zebra striping off by default (analysts scan by column); a 1px `--border-subtle` row rule instead.
- Row hover: `--bg-panel-alt`. Row click: opens a detail drawer, never a full navigation, so the analyst does not lose their filter context.
- Sort indicators in the header; multi-sort with shift-click.
- Virtualised above 200 rows (`@tanstack/react-virtual`); server-side pagination always.
- Empty state states *why* it is empty ("No observations match these filters" vs "Collection has not run for this route yet") — these are different problems and must not look identical.

### 4.7 Chart panels

Shared configuration across every chart:

| Aspect | Rule |
|---|---|
| Grid lines | Horizontal only, `--border-subtle`, 1px. No vertical grid. |
| Axes | `--text-xs`, `--text-muted`. Y-axis in INR with a thin-space thousands separator. |
| Y-axis zero | Include zero for bar charts; **never force zero** on index/price time-series (it destroys resolution) — instead label the axis range clearly. |
| Tooltip | Dark panel, all series at that x, values tabular, plus the observation count behind the point. |
| Legend | Top-right, horizontal, clickable to toggle series. |
| Baseline band | Expected-fare band rendered as a translucent `--accent-300` ribbon behind the actual line. |
| Confidence interval | Forecast bounds as a translucent band, with the point forecast as a dashed line beyond the last actual. |
| Annotations | Event markers (festivals, holidays) as thin vertical rules with a hover label. |
| Interaction | `dataZoom` brush on all time-series; crosshair on hover; export-to-PNG in the panel header. |
| Empty/low-n | If `n < min_observations`, the segment renders dotted and the footer says so. Never draw a confident line through thin data. |

### 4.8 Filter bar

Persistent, sticky under the page header:

```
[Date range v] [Routes v] [Airlines v] [Sources v] [Lead time v] [Quality >= 60 v]   [Reset]
```

- Multi-select popovers with search and select-all.
- Active filters render as removable chips beneath the bar.
- Filter state is serialised into the URL query string, so any view is shareable — important during judging, where a specific state needs to be returned to.

### 4.9 Methodology popover

Triggered from any `(i)` icon. Contains: what is measured, the formula in monospace, the estimator in use, the quality threshold applied, the weight-set version, and a link to the full Methodology page. This is the component that converts "trust us" into "check us".

---

## 5. Screen designs

### 5.1 Dashboard

```
+--------------------------------------------------------------------------------+
| Dashboard                                    [Date range: Last 30 days v]      |
| National airfare measurement - vintage 2026-09-01                              |
+--------------------------------------------------------------------------------+
| +-------------------------+ +----------+ +----------+ +----------+ +---------+ |
| | INDIA AIRFARE INDEX     | | ROUTES   | | AIRLINES | | OTA SRC  | | FLIGHTS | |
| |                         | | TRACKED  | |          | |          | | MONITORED|
| |  127.4                  | |          | |          | |          | |         | |
| |  ^ 7.4% MoM             | |   142    | |    12    | |     5    | | 18,742  | |
| |  [~~~~30d sparkline~~~] | | +6 new   | |          | | 5 online | | today   | |
| |  base 2025=100          | |          | |          | |          | |         | |
| +-------------------------+ +----------+ +----------+ +----------+ +---------+ |
|  cols 1-4                    5-6         7-8          9-10         11-12       |
+--------------------------------------------------------------------------------+
| +--------------------------------------------+ +-----------------------------+ |
| | AIRFARE INDEX TREND      [D][W][M][Y]  (i) | | AIRFARE PRESSURE MAP    (i) | |
| |                                            | |                             | |
| |   140 |                            /\      | |     [ India choropleth ]    | |
| |   130 |               /\      ____/  \     | |     route arcs coloured     | |
| |   120 |  ___/\___/\__/  \____/         \   | |     by pressure band        | |
| |   110 |/                                   | |                             | |
| |       +------------------------------------ | |  [] low [] med [] high     | |
| | Source: 8 sources · n=2.4M · q>=60         | | Source: index_values         | |
| +--------------------------------------------+ +-----------------------------+ |
|  cols 1-8                                        cols 9-12                     |
+--------------------------------------------------------------------------------+
| +----------------------------+ +---------------------------+ +---------------+ |
| | TOP PRICE INCREASES   (i)  | | TOP PRICE DECREASES  (i)  | | KEY INSIGHTS  | |
| |                            | |                           | |               | |
| | DEL-BOM   ^ 18.4%  10,450  | | BLR-HYD  v 6.2%    4,180  | | > DEL-BOM is  | |
| | BOM-GOI   ^ 14.1%   9,120  | | MAA-CCU  v 4.8%    5,340  | |   18% above   | |
| | DEL-SXR   ^ 12.7%  11,890  | | DEL-LKO  v 3.1%    3,960  | |   its 30-day  | |
| | BLR-DEL   ^  9.3%   7,240  | | BOM-PNQ  v 2.4%    2,880  | |   baseline.   | |
| | CCU-BOM   ^  8.8%   8,410  | | HYD-MAA  v 1.9%    3,120  | |               | |
| |                            | |                           | | > Last-minute | |
| | Source: route index, 7d    | | Source: route index, 7d   | |   premiums up | |
| +----------------------------+ +---------------------------+ +---------------+ |
|  cols 1-5                       cols 6-10                     cols 11-12       |
+--------------------------------------------------------------------------------+
```

Interaction: every mover row is a link to `/routes/{code}`; the highest-severity anomaly is highlighted with a severity left-border, which is the entry point into the guided demo path.

### 5.2 Route Intelligence — `/routes/DEL-BOM`

```
+--------------------------------------------------------------------------------+
| DEL -> BOM   Delhi (Indira Gandhi Intl) -> Mumbai (Chhatrapati Shivaji)         |
| Route index 131.4  ·  weight 18.0%  ·  region: North-West  ·  1,138 km          |
+--------------------------------------------------------------------------------+
| +-----------+ +-----------+ +-----------+ +-----------+ +-----------+          |
| | CURRENT   | | 7-DAY AVG | | 30-DAY AVG| | YEARLY AVG| | ROUTE IDX |          |
| | 10,450    | | 9,620     | | 8,150     | | 7,250     | | 131.4     |          |
| | ^ 8.6% WoW| |           | | ^12.3% MoM| | ^44.1% YoY| | ^ 12.3%   |          |
| +-----------+ +-----------+ +-----------+ +-----------+ +-----------+          |
+--------------------------------------------------------------------------------+
| +--------------------------------------------------------------------------+   |
| | FARE TREND WITH EXPECTED BASELINE                     [30d][90d][1y] (i) |   |
| |                                                                          |   |
| |  12k |                                        ,--*  <- observed          |   |
| |  10k |                          ,-----------''                           |   |
| |   8k |  ####################################  <- expected band (P25-P75) |   |
| |   6k |,--''                                                              |   |
| |      +--------------------------------------------------------------     |   |
| |       [ event markers: Diwali |  long weekend | ]                        |   |
| | Source: 8 sources · n=1,284 · q>=60 · estimator: trimmed mean (10%)      |   |
| +--------------------------------------------------------------------------+   |
+--------------------------------------------------------------------------------+
| +------------------------------+ +-------------------------------------------+ |
| | AIRLINE COMPARISON      (i)  | | OTA / SOURCE COMPARISON              (i)  | |
| |                              | |                                           | |
| | IndiGo      |=====|  6,200   | | Airline Direct        6,200               | |
| | Air India   |======| 7,100   | | MakeMyTrip            6,350  (+2.4%)      | |
| | AI Express  |====|   5,800   | | Goibibo               6,180  (-0.3%)      | |
| | Akasa       |=====|  6,050   | | Yatra                 6,420  (+3.5%)      | |
| | SpiceJet    |====|   5,900   | | Cleartrip             6,300  (+1.6%)      | |
| |  (box plots: median + IQR)   | | spread: 240 (3.9%)  ·  conv. fee delta    | |
| +------------------------------+ +-------------------------------------------+ |
+--------------------------------------------------------------------------------+
| +------------------------------+ +-------------------------------------------+ |
| | FARE COMPOSITION        (i)  | | ROUTE RISK PROFILE                   (i)  | |
| |                              | |                                           | |
| | Base fare        5,400  63%  | | Volatility score      HIGH   (CV 0.31)    | |
| | Taxes            1,120  13%  | | Anomalies (30d)       4                   | |
| | UDF                480   6%  | | Data completeness     98.2%               | |
| | Airport charges    390   5%  | | Sources active        7 / 8               | |
| | Convenience fee    210   2%  | | Avg quality score     91  HIGH            | |
| | ---------------------------  | |                                           | |
| | TOTAL CONSUMER   7,600 100%  | | [ 30-day volatility sparkline ]           | |
| |  [ stacked bar visual ]      | |                                           | |
| +------------------------------+ +-------------------------------------------+ |
+--------------------------------------------------------------------------------+
```

### 5.3 Lead-Time Intelligence

```
+--------------------------------------------------------------------------------+
| Lead-Time Intelligence          [Route: DEL-BOM v]  [Period: Last 30 days v]   |
+--------------------------------------------------------------------------------+
| +----------------------------------------+ +---------------------------------+ |
| | LEAD-TIME FARE CURVE              (i)  | | BOOKING WINDOW TABLE            | |
| |                                        | |                                 | |
| | 12k |                              *   | | Window   Avg fare   vs T+45     | |
| |     |                            /     | | -------------------------------- | |
| | 10k |                          /       | | T+45      5,200      baseline   | |
| |     |                        /         | | T+30      5,600      +7.7%      | |
| |  8k |                   ___/           | | T+15      6,300     +21.2%      | |
| |     |          ____----'               | | T+7       7,900     +51.9%      | |
| |  6k |*----*---'                        | | T+1      11,800    +126.9%      | |
| |     +--------------------------------- | |                                 | |
| |      T+45  T+30  T+15  T+7  T+1        | | Last-minute premium: +126.9%    | |
| |                                        | | Elasticity: -0.42               | |
| | Source: 8 sources · n=6,420 · q>=60    | | Early-booking advantage: 55.9%  | |
| +----------------------------------------+ +---------------------------------+ |
+--------------------------------------------------------------------------------+
| +--------------------------------------------------------------------------+   |
| | ELASTICITY BY ROUTE                                                  (i) |   |
| | Route      Elasticity   Last-min premium   Booking pressure   Curve      |   |
| | DEL-BOM      -0.42         +126.9%              HIGH          [~~~~]     |   |
| | DEL-BLR      -0.38          +98.4%              HIGH          [~~~~]     |   |
| | BOM-BLR      -0.29          +71.2%              MEDIUM        [~~~~]     |   |
| | Model-based estimate: OLS of ln(fare) on ln(lead_days)                   |   |
| +--------------------------------------------------------------------------+   |
+--------------------------------------------------------------------------------+
```

### 5.4 Anomaly Intelligence

```
+--------------------------------------------------------------------------------+
| Anomaly & Surge Intelligence     [Severity: All v] [Last 7 days v] [Route v]   |
+--------------------------------------------------------------------------------+
| ANOMALY FEED                          | ANOMALY DETAIL  (selected)              |
| ------------------------------------- | -------------------------------------- |
| |CRIT| DEL-BOM   +68.5%   2h ago      | DEL -> BOM   31 Aug 2026, 14:20 IST    |
| |HIGH| BOM-GOI   +42.1%   5h ago      |                                        |
| |HIGH| DEL-SXR   +38.7%   6h ago      | +----------------+ +----------------+  |
| |MED | BLR-DEL   +21.4%   9h ago      | | EXPECTED       | | OBSERVED       |  |
| |MED | CCU-BOM   +19.8%  11h ago      | | 6,200          | | 10,450         |  |
| |LOW | MAA-HYD   +11.2%  14h ago      | | (T+15 baseline)| | (this obs.)    |  |
| |                                     | +----------------+ +----------------+  |
| | [data-quality alerts shown in a     |                                        |
| |  separate tab so scraper failures   | DEVIATION  +68.5%      SEVERITY  HIGH  |
| |  are never mixed with market moves] |                                        |
| |                                     | CONTRIBUTING FACTORS                   |
| |                                     |  Weekend demand         |=====| 21%   |
| |                                     |  Low seat availability  |====|  18%   |
| |                                     |  Festival proximity     |===|   14%   |
| |                                     |  Short booking window   |==|    11%   |
| |                                     |  Unexplained residual   |=|      4%   |
| |                                     |  ------------------------------------  |
| |                                     |  (i) Model-based attribution. Shares   |
| |                                     |      are estimated, not measured.      |
| |                                     |                                        |
| |                                     | DETECTORS FIRED: z-score, MAD, IForest |
| |                                     | [ View contributing observations -> ]  |
+--------------------------------------------------------------------------------+
```

The **"Model-based attribution"** note is mandatory and always visible, not hidden behind a tooltip. Attributing causes is the most scientifically contestable thing this product does, and saying so plainly is what makes it credible rather than reckless.

### 5.5 CPI Augmentation Simulator

```
+--------------------------------------------------------------------------------+
| CPI Augmentation Simulator                                                     |
+--------------------------------------------------------------------------------+
| +--------------------------------------------------------------------------+   |
| | !  SIMULATION ONLY. This module is a simulation for analytical           |   |
| |    demonstration. It does not represent an official CPI revision or      |   |
| |    official NSO methodology.                                             |   |
| +--------------------------------------------------------------------------+   |
|   ^ persistent, non-dismissible, --warn-100 bg, --warn-700 text, top of page    |
+--------------------------------------------------------------------------------+
| +-------------+  +-------------+  +--------------+  +----------------------+   |
| | BASE CPI    |  | AIRFARE IDX |  | AIRFARE WT   |  | SIMULATED AUGMENTED  |   |
| |             |  |             |  |              |  |                      |   |
| | 142.1       |  | 158.7       |  |   2.5%       |  | 143.0                |   |
| | 2024-base   |  | our index   |  | [--o------]  |  | ^ 0.9 vs base CPI    |   |
| | (vintage    |  | 2025-base   |  |  slider      |  |                      |   |
| |  labelled)  |  |             |  |  0% - 10%    |  |                      |   |
| +-------------+  +-------------+  +--------------+  +----------------------+   |
+--------------------------------------------------------------------------------+
| +-----------------------------------------+ +--------------------------------+ |
| | SCENARIO FLOW                           | | SENSITIVITY                    | |
| |                                         | |                                | |
| |   Existing CPI  (142.1)                 | | Weight   Augmented   Delta     | |
| |         |                               | | 1.0%     142.3       +0.2      | |
| |         v                               | | 2.5%     143.0       +0.9      | |
| |   Airfare signal (158.7)                | | 5.0%     142.9       +1.7      | |
| |         |                               | | 7.5%     143.3       +2.4      | |
| |         v                               | | 10.0%    143.8       +3.2      | |
| |   Scenario weighting  (w = 2.5%)        | |                                | |
| |         |                               | | [ sensitivity curve chart ]    | |
| |         v                               | |                                | |
| |   Simulated augmented measurement       | | Formula:                       | |
| |         (143.0)                         | | Aug = CPI(1-w) + Airfare(w)    | |
| +-----------------------------------------+ +--------------------------------+ |
+--------------------------------------------------------------------------------+
```

The formula is printed on screen. A judge who wants to verify the arithmetic can do it in their head, which is exactly the intended effect.

### 5.6 Backtesting Lab

```
+--------------------------------------------------------------------------------+
| Backtesting Lab      [Window: 90 days v] [Routes: All v] [Estimator: median v] |
+--------------------------------------------------------------------------------+
| +-----------+ +-----------+ +-----------+ +-----------+ +-------------------+  |
| | CORRELATION| |   MAPE    | |    MAE    | |   RMSE    | | TREND ACCURACY    |  |
| |   0.91     | |   3.4%    | |    240    | |    318    | |      94%          |  |
| +-----------+ +-----------+ +-----------+ +-----------+ +-------------------+  |
+--------------------------------------------------------------------------------+
| +--------------------------------------------------------------------------+   |
| | OUR INDEX vs DGCA BENCHMARK                                          (i) |   |
| |                                                                          |   |
| | 140 |         ,-*-,          our index (solid)                           |   |
| | 130 |    ,-*-'    '-*        DGCA benchmark (dashed)                      |   |
| | 120 |,-*'  ' - . _ .-'                                                    |   |
| |     +------------|-------------------------------------------            |   |
| |     TRAIN        | TEST (out-of-sample, 90d)                              |   |
| |                  ^ split boundary, labelled                               |   |
| +--------------------------------------------------------------------------+   |
| +--------------------------------------------------------------------------+   |
| | RESIDUALS                        | ESTIMATOR COMPARISON                   |   |
| |  +2% |    |   |     |            | Estimator        MAPE   Corr           |   |
| |   0% |--|-|-|-|--|--|--|---      | Mean             5.8%   0.84           |   |
| |  -2% |  |     |                  | Median           3.9%   0.90           |   |
| |                                  | Trimmed mean 10% 3.4%   0.91  <- used  |   |
| |                                  | Weighted median  3.6%   0.91           |   |
| +--------------------------------------------------------------------------+   |
+--------------------------------------------------------------------------------+
```

The estimator comparison table is the design element that proves methodology was chosen empirically rather than by convenience — a direct answer to a likely judge question.

### 5.7 Forecasting

```
+--------------------------------------------------------------------------------+
| Forecasting          [Target: National index v]  [Horizon: 14 days v]          |
+--------------------------------------------------------------------------------+
| +-----------------------------------------+ +--------------------------------+ |
| | 14-DAY FORECAST WITH INTERVALS     (i)  | | EXPECTED AIRFARE PRESSURE      | |
| |                                         | |                                | |
| | 10k |                       ..#####     | |         H I G H                | |
| |     |                   ..######        | |                                | |
| |  9k |              ,---''####  <- 80% CI| | Forecast range                 | |
| |     |         ,---'    ..--- point fcst | |   7,900 - 9,200                | |
| |  8k |    ,---'      ..                  | |                                | |
| |     |___'                               | | Model: SARIMA (v2.1.0)         | |
| |     +--------------|------------------  | | Validation MAPE: 4.7%          | |
| |      actual        | forecast           | |                                | |
| +-----------------------------------------+ +--------------------------------+ |
| +--------------------------------------------------------------------------+   |
| | MODEL COMPARISON (walk-forward validation)                               |   |
| | Model                    MAPE    RMSE    Selected                        |   |
| | Seasonal moving average  8.2%     640                                    |   |
| | Exponential smoothing    5.9%     498                                    |   |
| | SARIMA                   4.7%     412      <- selected                   |   |
| | Gradient boosting        4.9%     428                                    |   |
| +--------------------------------------------------------------------------+   |
+--------------------------------------------------------------------------------+
```

A point forecast never appears without its band. This is enforced in the chart component itself — it will not render a forecast series unless bounds are supplied.

### 5.8 Data Explorer

```
+--------------------------------------------------------------------------------+
| Data Explorer     [Raw | Cleaned]     [Filters: 3 active]      [Export CSV v]  |
+--------------------------------------------------------------------------------+
| [Date range v][Route v][Airline v][Source v][Class v][Lead v][Quality >=60 v]  |
| Active: (DEL-BOM x) (IndiGo x) (T+15 x)                             [Reset]    |
+--------------------------------------------------------------------------------+
| TIMESTAMP        ORG DST AIRLINE FLIGHT  DEP DATE  LEAD CLASS  BASE  TAX  FEE  |
|                                                          TOTAL SOURCE  QUALITY |
| 2026-08-30 09:14 DEL BOM IndiGo  6E-2134 15 Sep    16   ECO   5,400 1,120  210 |
|                                                          6,800 MMT     [==] 94 |
| 2026-08-30 09:14 DEL BOM IndiGo  6E-2134 15 Sep    16   ECO   5,400 1,120    0 |
|                                                          6,590 Direct  [==] 97 |
| ...                                                                            |
+--------------------------------------------------------------------------------+
| Showing 1-100 of 48,213      [< prev]  page 1 of 483  [next >]                 |
+--------------------------------------------------------------------------------+
```

Row click opens a right-hand drawer showing the full observation, its raw payload, the quality-factor breakdown that produced the score, and which pipeline steps modified it. This is the auditability promise made tangible.

### 5.9 API Portal

Two-pane layout: endpoint list on the left, endpoint detail on the right with parameters, a live "try it" panel, a copyable `curl` example, and a sample response. Key management (create, revoke, view rate limit and quota) sits in a separate tab for `admin` role.

### 5.10 Collection Engine

Per-source status cards showing: source name and type, status dot (online / degraded / unavailable), last run time, records found/valid/failed, rolling success rate sparkline, next scheduled run. A run-history table beneath with filters. Admin-only manual trigger buttons. Data-quality flags surface here, deliberately separated from market anomalies.

---

## 6. Iconography

- **Library:** Lucide (consistent 1.5px stroke, geometric, neutral).
- **Sizes:** 16px inline, 20px navigation, 24px section headers.
- **Never** use emoji in the product UI. The navigation glyphs in the source spec are shorthand for the doc, not a design instruction — a government statistical portal with emoji navigation loses credibility instantly.

| Concept | Icon |
|---|---|
| Dashboard | `layout-dashboard` |
| Index | `trending-up` |
| Routes | `plane` |
| Anomalies | `alert-triangle` |
| Lead time | `calendar-clock` |
| CPI simulator | `calculator` |
| Backtest / forecast | `line-chart` |
| Data explorer | `database` |
| Collection | `radio-tower` |
| API portal | `plug` |
| Reports | `file-text` |
| Settings | `settings` |
| Methodology info | `info` |
| Quality | `shield-check` |

---

## 7. Content and voice

| Rule | Do | Don't |
|---|---|---|
| Be precise | "Fares on DEL-BOM are 18.4% above the 30-day baseline." | "Prices are skyrocketing!" |
| Attribute estimates | "Model-based attribution." | Presenting attribution as measurement |
| State the basis | "+7.4% MoM (base 2025 = 100)" | "+7.4%" |
| Use INR properly | "INR 10,450" or the rupee glyph with tabular numerals | "10450" or "Rs.10450/-" |
| Route notation | `DEL - BOM` in mono, city names spelled out on detail pages | "Delhi to Mumbai flight prices" |
| Time | IST with the zone stated, ISO 8601 in API and exports | Ambiguous local times |
| Empty states | Say what is missing and why | "No data" |

Number formatting: Indian digit grouping (`10,450` / `2,40,000`) in the UI; plain machine numbers in exports and API.

---

## 8. Accessibility (WCAG 2.1 AA)

| Area | Requirement |
|---|---|
| Contrast | Body text 4.5:1 minimum; large text and UI components 3:1. Verified in both themes. |
| Colour independence | Direction is also encoded by arrow glyph and sign; severity also by left-border weight and text label; quality also by numeric score. No information is colour-only. |
| Keyboard | Full keyboard operation. Visible 2px `--border-focus` ring. Logical tab order. Skip-to-content link. |
| Charts | Each chart has an accessible name, a text summary, and a "view as table" toggle exposing the underlying series to screen readers. |
| Tables | Proper `<th scope>`, caption, and `aria-sort` on sortable headers. |
| Live regions | Data-mode changes and new critical anomalies announced via `aria-live="polite"`. |
| Motion | All non-essential animation removed under `prefers-reduced-motion`. |
| Zoom | Layout remains usable at 200% zoom. |
| Targets | Minimum 32x32px interactive targets (compact table rows use a 36px row with full-row hit area). |

---

## 9. Component inventory (build checklist)

**Primitives (shadcn/ui base):** Button, Input, Select, Checkbox, Radio, Switch, Slider, Tabs, Tooltip, Popover, Dialog, Drawer, Dropdown, Badge, Skeleton, Toast, Separator, ScrollArea.

**Domain components (custom):**

| Component | Used by |
|---|---|
| `KpiCard` / `HeroKpiCard` | Dashboard, Index, Route |
| `DeltaChip` | Everywhere numeric change is shown |
| `SeverityBadge` | Anomalies, Route risk |
| `QualityIndicator` | Data Explorer, panel footers |
| `DataModeBadge` | App top bar |
| `PanelShell` (header + content + source footer) | Every analytical panel |
| `MethodologyPopover` | Every `(i)` affordance |
| `IndexTrendChart` | Dashboard, Index |
| `FareTrendChart` (with baseline band) | Route |
| `LeadTimeCurveChart` | Lead-time, Route |
| `ForecastChart` (requires bounds) | Forecasting |
| `BenchmarkOverlayChart` + `ResidualChart` | Backtesting |
| `PressureMap` (ECharts geo, bundled GeoJSON) | Dashboard |
| `AirlineBoxPlot` / `SourceSpreadChart` | Route |
| `FareCompositionBar` | Route |
| `AttributionBars` | Anomalies |
| `MoversList` | Dashboard |
| `InsightsPanel` | Dashboard |
| `ObservationTable` (virtualised) | Data Explorer |
| `FilterBar` + `FilterChips` | Explorer, Anomalies, Lead-time |
| `SourceStatusCard` | Collection Engine |
| `EndpointDoc` / `TryItPanel` | API Portal |
| `DisclaimerBanner` | CPI Simulator |
| `ScenarioSlider` + `SensitivityTable` | CPI Simulator |

---

## 10. Implementation notes

- **Tokens are the single source of truth.** Define them once in `styles/tokens.css`, map them into `tailwind.config.ts` via CSS variables, and generate the ECharts and Plotly themes from the same file (`lib/charts/theme.ts`). A colour must never be typed literally into a component.
- **Charts read tokens at runtime**, not build time, so theme switching recolours charts without a remount.
- **`PanelShell` enforces the source footer** by making `source`, `count` and `qualityThreshold` required props. A panel physically cannot be built without declaring its provenance — the design principle is compiled in, not documented and hoped for.
- **`ForecastChart` requires `lower` and `upper` props.** TypeScript will not allow a bare point forecast.
- **India GeoJSON is bundled locally** (`public/geo/india.json`) — no tile server, so the map works with the network disabled during judging.
- **Font loading:** Inter and JetBrains Mono self-hosted via `next/font` with `display: swap`. No external font CDN, for the same offline reason.
