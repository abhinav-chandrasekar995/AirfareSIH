# RBI APIx Module — Decision Log

Split out from `IMPLEMENTATION_LOG.md` (500+ entries, genuinely overloaded) specifically
for the Core/Headline APIx split, the RBI policy dashboard additions, and the inflation
alert system. Same rigor, same "why," just its own file so it stays navigable. Cross-
references `IMPLEMENTATION_LOG.md` where relevant (e.g. the existing index engine,
weights, and CPI simulation this builds on).

## 0. Scope, agreed before writing any code

A teammate proposed three modules (index engine with Core/Headline fare separation,
an RBI policy simulator dashboard, and a real-time inflation alert system). Checked
against the actual codebase before agreeing to anything - most of it already existed:

- Base fare / taxes / total fare are already separate columns in `fare_observations`.
- The Laspeyres formula, DGCA route weights, and backtest validation (corr=0.9959 vs
  real DGCA data) already exist and are already correct.
- `app/analytics/lead_time/` and `app/analytics/cpi/` already exist.
- `/reports` already generates real CSVs from live data - a new report type is a small
  addition, not new infrastructure.

**One real conflict surfaced and resolved**: the teammate's proposed route weights
(DEL-BOM=0.35, DEL-BLR=0.25, BOM-BLR=0.20) do not match the actual seeded,
DGCA-calibrated weights already in the database (DEL-BOM=0.18, DEL-BLR=0.15,
BOM-BLR=0.12, all 15 routes summing to 1.0). The existing weights are what the 0.9959
backtest correlation was computed against. **Decision: keep the existing weights.**
Swapping them in without re-validating the backtest would quietly break the one number
most likely to be scrutinized by judges.

**Scope agreed for the demo (tomorrow), ranked by impact/risk:**

Building:
1. Core APIx (base-fare-only) as a second series alongside the existing Headline
   (total-fare-based) series - additive, not a rewrite of the existing `index_values`.
2. Price breakdown card (avg base fare / taxes+fees / total fare).
3. Policy-band reference lines on the trend chart.
4. Core/Headline toggle.
5. WoW Core APIx threshold alert + banner.
6. "Generate RBI Policy Brief" report.

Explicitly deferred, not silently dropped:
- **ATF fuel-tax slider** - needs an invented pass-through coefficient with no real data
  behind it. Doable later as a clearly-labeled simulation (same disclaimer pattern as
  the existing CPI simulator); rushing an unvalidated economic assumption in the night
  before a demo is the wrong tradeoff.
- **Lead-time-reweighted index toggle** - changes index *methodology* via a UI control.
  Same reasoning as the weights conflict above: this is exactly the kind of change that
  needs re-validation against DGCA before it ships, not a same-day addition.

## 1. Backend: Core APIx series (item 1)

New, additive layer end to end - nothing in the existing DGCA-backtested Headline path
was touched. One new table, one new model, one new repository, one new backfill script.

- **`app/db/models/derived.py`**: added `CoreIndexValue`, a structural mirror of the
  existing `IndexValue` (same columns), `__tablename__ = "core_index_values"`. A
  separate table rather than a `fare_basis` column/flag on `IndexValue` - keeps every
  existing query against `IndexValue` (dashboard, routes, forecast, backtest, anomalies)
  exactly as-is, with zero risk of an accidental extra row showing up in an unfiltered
  query.
- **`alembic/versions/0004_add_core_index_values.py`**: creates the table, an index on
  `date`, and the same RLS pattern as every other derived table (`ENABLE`/`FORCE ROW
  LEVEL SECURITY`, `_public_read` SELECT-true policy, `_elevated_write` ALL policy gated
  on `current_setting('app.role') IN ('ANALYST','ADMIN')`). Applied clean:
  `alembic upgrade head` (0003 -> 0004), verified via psql.
- **`scripts/compute_core_apix.py`**: backfills the whole series in one pass. Reuses the
  *exact same* `compute_route_measure` / `compute_route_index` / `compute_aggregate_index`
  functions the Headline series uses - the only difference is feeding them `base_fare`
  instead of `total_fare`. This matters for the demo story: Core and Headline aren't two
  different models, they're the same validated engine run on two different fare columns.
  - **Bug caught before it reached the UI**: first run computed across the full 403-day
    raw history instead of matching the Headline series' 120-day window. A Core/Headline
    toggle needs a consistent x-axis, so this would have made the toggle visibly break.
    Fixed by importing the seed's own `TODAY` constant and applying the identical
    `SPAN_START = TODAY - timedelta(days=120)` filter Headline's own seed script uses.
  - **Final result**: 121,793 raw observations processed, base measures computed for all
    15 routes, **2,450 `core_index_values` rows persisted across 123 dates** (Headline
    has 122 - the one extra date is 2026-09-02, which Core has data for and Headline has
    a real gap on; not a bug, Headline's live-collection script simply never touched it).
  - Latest NATIONAL Core APIx: 2026-09-03 = 121.209 (Headline, same date = 117.749 -
    genuinely different numbers, confirming the Core/Headline split is methodologically
    real and not a no-op).
- **`app/db/repositories/core_index_repository.py`**: same query shape as
  `index_repository.py` (`_base_query`/`series`/`latest`/`value_on_or_before`), same
  "no baked-in `.order_by()` before filters are applied" discipline that
  `index_repository.py` already documents (from an earlier bug, see
  `IMPLEMENTATION_LOG.md` D-065).

## 2. Backend: price breakdown, comparison, and alert (items 2 and 5)

- **`app/services/apix_service.py`**: new service, deliberately not folded into
  `index_service.py`/`dashboard_service.py`, same "don't touch validated code paths"
  principle.
  - `get_core_series` / `get_comparison` - Core alone, and Core+Headline aligned by date
    for the toggle chart (two independent queries, not a SQL join - the tables have no
    FK relationship by design).
  - `get_price_breakdown` - avg base fare / avg(taxes+udf+airport_charges+convenience_fee)
    / avg total fare / n, for the most recent date with any observations.
  - `get_alert_status` - the WoW inflation check. Two independent trigger conditions:
    national Core APIx WoW > 6.0% ("`WOW_ALERT_THRESHOLD_PCT`"), or any single route's
    Core APIx WoW > 20.0% ("`ROUTE_SPIKE_THRESHOLD_PCT`") - both from the teammate's spec.
    Whichever condition is larger in magnitude drives the banner message, using the
    teammate's exact requested wording for both the route-spike and national-WoW cases.
    Deliberately a *different* comparison window than the existing anomaly detector
    (which compares against a lead-time-conditioned 10-60-day baseline) - this answers
    "how much did the headline policy number move in the last week," not a per-
    observation data-quality question.
- **`app/api/v1/routers/apix.py`**: new `/api/v1/apix/*` namespace (not an extension of
  `/index`), 4 GET endpoints: `/core`, `/comparison`, `/price-breakdown`, `/alert`.
  Registered in `app/api/v1/router.py` right after `index.router`.
- **Live verification (curl, against the real DB, after a server restart)**:
  - `/apix/core?level=NATIONAL`: 123 points, ends 2026-09-03 = 121.209.
  - `/apix/comparison`: core[-1]=121.209, headline[-1]=117.749, same date - confirms the
    split produces genuinely different numbers.
  - `/apix/price-breakdown`: `{as_of: 2026-09-03, avg_base_fare: 5753.02,
    avg_taxes_and_fees: 2237.28, avg_total_fare: 7990.3, n_observations: 1493}`.
  - `/apix/alert`: **real, non-scripted result** -
    `{triggered: true, status: "HIGH_INFLATION_RISK", national_wow_pct: -2.74,
    spiking_route: "BLR-HYD", spiking_route_wow_pct: 49.18, message: "INFLATION WARNING:
    Severe base-fare volatility detected on BLR-HYD. Core APIx projected to breach RBI
    tolerance band (+49.2% WoW)."}`. National WoW did NOT trip its own threshold
    (-2.74%, below +6%) but BLR-HYD's route-level spike did (49.18% > 20%) - the alert
    logic correctly distinguishes and prioritizes the two trigger types instead of only
    ever firing on the national number. BLR-HYD is also the route that showed the
    highest pressure in yesterday's live SerpApi collection, so this is a genuine
    finding, not noise from the synthetic seed.

## 3. Backend: "Generate RBI Policy Brief" report (item 6)

- **`app/api/v1/routers/reports.py`**: added `GET /api/v1/reports/rbi-policy-brief`,
  same `_csv_response()` helper every other report in this file uses. Assembled from
  the *exact same* `apix_service` functions the live endpoints call (`get_alert_status`,
  `get_price_breakdown`, `get_comparison`) - per this file's own stated design principle,
  a report can never show a number the interactive pages don't already show. One CSV:
  alert status/thresholds/message, Core vs Headline national figures, and the price
  breakdown, all for the same `as_of` date.
- Verified live: `curl .../reports/rbi-policy-brief` returns a correct CSV with the same
  real numbers as the live `/apix/*` endpoints above.

## 4. Verification

Ran the same suite used throughout the rest of this project on every new/touched file
(`reports.py`, `apix.py`, `apix_service.py`, `core_index_repository.py`, `derived.py`,
`db/models/__init__.py`, `router.py`):
- `ruff check` - all checks passed.
- `lint-imports` - 1 contract kept, 0 broken (analytics layer boundary untouched).
- `pytest -q` - 83 passed, 17 skipped (pre-existing skips, unrelated), 0 failed.

## 5. Frontend: RBI Policy & Elasticity Simulator page (items 2-6)

New page at `/rbi-policy`, added to the sidebar nav (`Landmark` icon, right after
"CPI Simulator" - same tier as the other simulator page). Same page-composition
pattern as the existing `/cpi-simulator` page: `PageHeader` + `PanelShell` +
`KpiCard`, loading/error states via the shared `Skeleton`/`ErrorState`/`EmptyState`
components, data via new `react-query` hooks in `lib/api/hooks.ts`
(`useApixComparison`, `usePriceBreakdown`, `useApixAlert` - 30s staleTime, alert also
`refetchInterval`d, since it's the one thing meant to feel live).

- **`types/api.ts`**: added `ApixPoint` (narrower than `IndexPoint` - the apix
  endpoints don't return estimator/weight/notes), `ApixComparison`,
  `PriceBreakdown`, `ApixAlert`.
- **`components/charts/ApixTrendChart.tsx`**: Core/Headline trend chart with RBI
  tolerance bands drawn as ECharts `markLine`s at base×1.04 and base×1.06 (base=100
  convention, matching how the rest of the app already presents the index - "base
  X=100"). **Deliberately labelled as a different lens than the WoW alert** - the
  bands here are a level-vs-base proxy, not the same computation as
  `/apix/alert`'s week-over-week check, and conflating the two would misrepresent
  the methodology. This mapping (4%/6% -> 104/106) was reasoned through, not
  confirmed against a specific RBI document - flagged here for anyone reviewing.
- **`components/kpi/PriceBreakdownCard.tsx`**: base-fare-vs-taxes proportional bar
  + total, from `/apix/price-breakdown`.
- **`components/rbi/InflationAlertBanner.tsx`**: two states - quiet "Normal" strip,
  or (when `alert.triggered`) a persistent (non-dismissible, `role="alert"`) banner
  in signal-red showing the exact backend-generated message, with a "Generate RBI
  Policy Brief" button linking directly to `/backend/api/v1/reports/rbi-policy-brief`.
- **`app/(app)/rbi-policy/page.tsx`**: assembles all of the above - alert banner up
  top, 4 KPI cards (Core APIx, Headline APIx, National WoW, Alert Status), then the
  trend chart (with a Core/Headline segmented-button toggle in the panel header) next
  to the price breakdown card and a second policy-brief button.
- **`app/(app)/reports/page.tsx`**: added "RBI Policy Brief" to the existing report
  template list (same `<a href>` download pattern every other report already uses -
  no new infrastructure).
- **Verification**: `tsc --noEmit` clean (one real bug caught and fixed: `??` and
  `||` mixed without parentheses in `PriceBreakdownCard.tsx`, a TS5076 error, not a
  logic bug - fixed by adding parens). `next lint` has no ESLint config in this
  project (pre-existing, unrelated to this work) so it was not run. Confirmed the
  page and its data both resolve for real, end to end, through the Next.js rewrite
  proxy: `curl localhost:3000/rbi-policy` → 200, sidebar link renders; `curl
  localhost:3000/backend/api/v1/apix/comparison` and `/apix/alert` → 200 with the
  same real numbers verified against the backend directly in §2 (BLR-HYD spike,
  -2.74% national WoW, etc.). Browser-side visual check not done in this session
  (no headed browser available) - the data path and route resolution are confirmed
  live; a human should eyeball it before the demo.

## 6. Remaining

- Human visual pass on `/rbi-policy` in an actual browser before the demo (chart
  legibility, markLine label placement, banner wrapping on narrow widths).
- Everything else from the original scope (§0) is done: Core/Headline split, price
  breakdown, policy bands, toggle, WoW alert + banner, Policy Brief report - all
  built, wired, and verified against live data.
- ATF fuel-tax slider and lead-time-reweighted toggle remain explicitly deferred
  (§0) - not revisited.
