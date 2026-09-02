# Product Requirements Document
## INDIA AIRFARE INTELLIGENCE
### Real-Time Airfare Price Index & CPI Augmentation Platform

| Field | Value |
|---|---|
| Document | Product Requirements Document (PRD) |
| Version | 1.0 |
| Status | Baseline for SIH build |
| Owner | Product / Team Lead |
| Last updated | 2026-09-01 |
| Related docs | [Architecture](02-ARCHITECTURE.md) · [Design](03-DESIGN.md) · [Schema](04-BACKEND-SCHEMA.md) · [Folder Structure](05-FOLDER-STRUCTURE.md) |

---

## 1. Overview

### 1.1 Product summary

India Airfare Intelligence is a **statistical intelligence platform**, not a flight-booking product. It continuously collects airfare observations from airline websites and Online Travel Aggregators (OTAs), normalises and quality-scores them, constructs a transparent route-weighted **India Airfare Price Index**, explains abnormal price movements, models booking-window (lead-time) effects, validates itself against DGCA published benchmarks, forecasts near-term price pressure, and demonstrates how a high-frequency airfare signal could augment CPI-related analysis.

### 1.2 One-line positioning

> A high-frequency, transparent, auditable measurement layer for India's domestic airfare market — built for policymakers, statisticians and regulators.

### 1.3 The product philosophy

```
Collect -> Clean -> Measure -> Explain -> Validate -> Predict -> Augment
```

### 1.4 What this product is NOT

| Not this | Because |
|---|---|
| A flight-booking site | We measure the market; we never sell a seat. No booking flow, no cart, no PNR. |
| A generic scraper + line chart | The value is the *index methodology*, the *quality framework* and the *validation*, not the scrape. |
| A claim that MoSPI does not collect online airfare | MoSPI CPI 2024 (base 2024=100, HCES 2023-24 weights, COICOP 2018) already uses alternative/digital sources. We position as an **augmentation and simulation layer**. |
| An official CPI revision | The CPI module is explicitly a *simulation for analytical demonstration*, labelled as such in the UI and in every API response. |

---

## 2. Problem statement

### 2.1 The SIH ask

The problem statement calls for an end-to-end software platform that can:

1. Automatically collect airfares from major airline websites and OTAs.
2. Cover a representative basket of city-pairs, informed by DGCA passenger-traffic data.
3. Capture **multiple advance-purchase windows** (T+1, T+7, T+15, T+30, T+45).
4. Handle JavaScript-rendered pages, session management and anti-bot conditions **ethically**.
5. Clean, normalise and de-duplicate messy multi-source fare data.
6. Separate fare components: base fare, taxes, UDF, airport charges, convenience fee.
7. Construct and visualise an airfare price index.
8. Expose results through an authenticated, documented API for NSO/RBI-style consumers.
9. Back-test for **at least 30 days** against publicly available DGCA monthly average-fare data.

### 2.2 The gap we actually close

| Gap | Consequence today | Our answer |
|---|---|---|
| Airfare is measured at low frequency | Periodic snapshots miss surges entirely | Daily (multi-times-daily) observation cadence |
| Fares are quoted, not decomposed | The consumer-facing total is obscured | Full fare-component decomposition |
| Lead time is ignored | A "Delhi-Mumbai fare" is meaningless without a booking window | Five fixed advance-purchase windows, modelled as a curve |
| Anomalies are unexplained | A spike is visible but not attributable | Baseline model + contributing-factor attribution |
| No auditability | Index numbers cannot be reproduced | Per-observation quality scores + open methodology page + Data Explorer |
| No external validation | Claims are unfalsifiable | DGCA back-test with MAE/RMSE/MAPE/correlation/directional accuracy |

---

## 3. Goals and non-goals

### 3.1 Product goals

| # | Goal | Success looks like |
|---|---|---|
| G1 | Produce a defensible national airfare index | Published daily, reproducible, methodology documented |
| G2 | Explain price movements, not just display them | Every HIGH-severity anomaly carries factor attribution |
| G3 | Prove correctness against an external benchmark | 30+ day back-test vs DGCA with reported error metrics |
| G4 | Be machine-consumable | Versioned REST API with auth, rate limits, OpenAPI docs |
| G5 | Be demo-proof | Dashboard fully functional with zero live network access |
| G6 | Be ethical by construction | robots.txt awareness, rate limits, no access-control bypass |

### 3.2 Explicit non-goals (v1)

- Booking, payment, seat selection, or any transaction.
- International routes (domestic India only in v1).
- Cargo, charter, or non-scheduled aviation.
- Real-time (sub-minute) streaming price feeds.
- Passenger PII of any kind — the system stores **zero personal data**.
- Bypassing CAPTCHAs, login walls, or any access control.

---

## 4. Target users and personas

| Persona | Role | Primary need | Key modules |
|---|---|---|---|
| **Statistical Officer (MoSPI/NSO)** | Constructs price indices | A transparent, reproducible, benchmark-validated airfare signal | Index, Methodology, Backtesting, CPI Simulator |
| **Aviation Regulator Analyst (DGCA)** | Monitors market conduct | Surge detection with route/airline attribution, evidence trail | Anomaly Intelligence, Route Intelligence, Reports |
| **Macroeconomist (RBI / think tank)** | Inflation nowcasting | High-frequency series via API, historical depth | API Portal, Index, Forecasting |
| **Partner Data Engineer** | Integrates the feed | Stable schemas, pagination, rate limits, changelogs | API Portal, Data Explorer |
| **SIH Judge / Evaluator** | Assesses in ~10 minutes | A single coherent story from raw fare to policy insight | The full guided demo path |

---

## 5. Feature requirements

Priority: **P0** = must ship for SIH demo · **P1** = should ship · **P2** = nice-to-have.

### 5.1 Module map

| # | Module | Priority |
|---|---|---|
| M1 | Dashboard (executive command centre) | P0 |
| M2 | Airfare Price Index (national / regional / route / airline) | P0 |
| M3 | Route Intelligence | P0 |
| M4 | Lead-Time Intelligence | P0 |
| M5 | Anomaly & Surge Intelligence | P0 |
| M6 | Event & Seasonal Intelligence | P1 |
| M7 | Airfare Volatility Engine | P1 |
| M8 | Airline & OTA Price Divergence | P1 |
| M9 | CPI Augmentation Simulator | P0 |
| M10 | Backtesting Lab (DGCA validation) | P0 |
| M11 | Forecasting Engine | P0 |
| M12 | Data Explorer | P1 |
| M13 | API Portal | P0 |
| M14 | Collection Engine control & monitoring | P1 |
| M15 | Reports | P2 |
| M16 | Settings & admin | P2 |

---

### M1 — Dashboard `P0`

**Purpose.** One screen that answers "what is happening to Indian airfares right now?"

**Requirements**

- **FR-M1-1** Display six live KPI cards: India Airfare Index (with MoM delta and direction), Routes Tracked, Airlines Covered, OTA Sources, Flights Monitored, Total Data Points.
- **FR-M1-2** All KPI values are computed from the database at request time. No hardcoded numbers anywhere in the shipped build.
- **FR-M1-3** Render an **Airfare Index Trend** chart with selectable granularity: daily / weekly / monthly / yearly.
- **FR-M1-4** Render **Top 5 Price Increases** and **Top 5 Price Decreases** by route over a selectable window (7d / 30d), each row linking to that route's page.
- **FR-M1-5** Render an **Airfare Pressure Map** of India: city-pairs coloured by pressure band (high / medium / low), derived from deviation-from-baseline.
- **FR-M1-6** Render an auto-generated **Key Insights** panel: 3-5 natural-language statements produced from computed statistics (template-filled from real values, never invented).
- **FR-M1-7** A data-freshness indicator showing the latest successful collection timestamp per source, and a visible badge when any displayed series includes replayed/cached data.

**Acceptance criteria**
- Dashboard renders complete in under 2.5 s on a warm cache.
- Every KPI is traceable: clicking it navigates to the module that computes it.
- With the network disabled, the dashboard renders fully from stored data and shows the cached-data badge.

---

### M2 — Airfare Price Index `P0`

**Purpose.** The statistical heart of the product.

**Requirements**

- **FR-M2-1** Compute a **National Index** against a declared base period (base = 100).
- **FR-M2-2** Compute **Regional Indices** for North / South / East / West India.
- **FR-M2-3** Compute **Route Indices** for every route in the active basket.
- **FR-M2-4** Compute **Airline Indices** (fare level per airline, normalised).
- **FR-M2-5** Route weights derive from DGCA passenger-traffic data; weights are stored, versioned and displayed in the UI.
- **FR-M2-6** Route-level price measure uses **robust statistics** — the system computes mean, median, trimmed mean and weighted median, and the configured estimator is recorded with each index value.
- **FR-M2-7** A **Methodology** page states, in plain language and formulas: basket definition, weight source and vintage, estimator choice and justification, base period, aggregation formula, and treatment of missing routes.
- **FR-M2-8** Every index value is reproducible: given the stored observations and the stored methodology version, recomputation yields an identical number.

**Index formulation (v1)**

```
Route price measure   P(r,t)  = robust_estimator( total_fare of valid observations on route r in period t )
Route index           I(r,t)  = ( P(r,t) / P(r,base) ) x 100
National index        I(t)    = SUM_r [ I(r,t) x w(r) ] / SUM_r w(r)     (Laspeyres-style, fixed weights)
```

Missing-route handling: if a route has no valid observations in period *t*, it is **excluded and weights are renormalised** over the observed set; the exclusion is recorded in `index_values.notes`.

**Acceptance criteria**
- Index recomputation over the same input produces an identical value.
- Methodology page passes the "hand the judge the formula" test — a reader can reproduce one route index with a calculator.

---

### M3 — Route Intelligence `P0`

**Purpose.** A dedicated analytical page per city-pair.

**Requirements**

- **FR-M3-1** Header stats: current average fare, 7-day average, 30-day average, yearly average, route index, MoM change %, YoY change %.
- **FR-M3-2** Fare trend chart with a selectable date range and an overlaid expected-baseline band.
- **FR-M3-3** **Airline comparison** — fare distribution per carrier on the route (IndiGo, Air India, Air India Express, Akasa, SpiceJet, and others).
- **FR-M3-4** **OTA comparison** — same itinerary priced across Airline Direct, MakeMyTrip, Goibibo, Yatra, Cleartrip, EaseMyTrip, Ixigo.
- **FR-M3-5** **Fare composition** breakdown: base fare + taxes + UDF + airport charges + convenience fee = final consumer fare, shown as a stacked bar and a table.
- **FR-M3-6** **Route risk** panel: volatility score, anomaly frequency, data-coverage completeness.
- **FR-M3-7** All route pages are deep-linkable: `/routes/DEL-BOM`.

**Acceptance criteria**
- Fare composition sums exactly to the recorded total fare, or the row is flagged by the tax-consistency quality check.

---

### M4 — Lead-Time Intelligence `P0`

**Purpose.** Model how booking timing drives price — a direct PS requirement.

**Requirements**

- **FR-M4-1** Collect and store observations at exactly five advance-purchase windows: **T+1, T+7, T+15, T+30, T+45**, where T is the departure date.
- **FR-M4-2** Render the **Lead-Time Fare Curve** per route and nationally.
- **FR-M4-3** Compute and display: last-minute premium (T+1 vs T+45, %), early-booking advantage, booking-pressure score, route-specific fare elasticity w.r.t. lead time, seasonal elasticity variation.
- **FR-M4-4** The lead-time curve feeds the anomaly baseline — an observation is compared against the expected fare *for its own lead-time bucket*, never against a lead-time-agnostic average.

**Elasticity definition (v1)**

```
elasticity(r) = d ln(fare) / d ln(lead_days)      estimated by OLS over the route's window observations
last_minute_premium = ( P(T+1) - P(T+45) ) / P(T+45) x 100
```

**Acceptance criteria**
- Each of the 5 windows has at least 1 observation per active route per collection day, or the gap is logged and surfaced in Data Quality.

---

### M5 — Anomaly & Surge Intelligence `P0`

**Purpose.** The primary differentiator — detect *and explain* abnormal fares.

**Requirements**

- **FR-M5-1** Establish an expected-fare baseline per (route, lead-time bucket, day-of-week, season).
- **FR-M5-2** Detect deviations using multiple methods and record which fired: **Z-score, IQR, MAD, Isolation Forest**.
- **FR-M5-3** Classify severity: LOW / MEDIUM / HIGH / CRITICAL by deviation magnitude and persistence.
- **FR-M5-4** Produce **contributing-factor attribution** per anomaly (weekend demand, low seat availability, festival proximity, short booking window, residual "other"), each contribution computed from data and **clearly labelled as model-based attribution**.
- **FR-M5-5** Maintain a searchable anomaly history with resolution status.
- **FR-M5-6** Detect **scraper anomalies** distinctly from market anomalies — a source returning an identical fare across thousands of observations must raise a *data-quality* alert, not a market surge.

**Acceptance criteria**
- No anomaly is shown without an expected value, an observed value, a deviation %, and a factor breakdown summing to 100%.
- A synthetic injected surge is detected within one pipeline cycle.

---

### M6 — Event & Seasonal Intelligence `P1`

- **FR-M6-1** Maintain an event calendar: festivals, national holidays, long weekends, major travel periods, seasonal peaks.
- **FR-M6-2** Compute normal-period vs event-period fare differentials per route.
- **FR-M6-3** Expose event proximity as a feature to the anomaly baseline and the forecaster.

---

### M7 — Airfare Volatility Engine `P1`

- **FR-M7-1** Compute per route: standard deviation, coefficient of variation, rolling volatility (7d / 30d), price range, abnormal-movement frequency.
- **FR-M7-2** Publish a composite **Airfare Volatility Score** with LOW / MEDIUM / HIGH banding.

---

### M8 — Airline & OTA Price Divergence `P1`

- **FR-M8-1** Compare the same itinerary (route + flight + departure datetime + fare class) across all sources observed within a matching window.
- **FR-M8-2** Report source-to-source spread, convenience-fee delta, discount detection, and inconsistency flags.
- **FR-M8-3** Feed divergence outliers into the data-quality framework as a cross-source validation signal.

---

### M9 — CPI Augmentation Simulator `P0`

**Purpose.** The policy-facing hero feature.

**Requirements**

- **FR-M9-1** Display Base CPI, Airfare Index, configurable Airfare Weight (%), and the resulting Simulated Augmented Index.
- **FR-M9-2** Allow scenario analysis: adjust the weight and observe sensitivity; compare multiple scenarios side by side.
- **FR-M9-3** Display the flow: Existing CPI -> Airfare signal -> Scenario weighting -> Simulated augmented measurement.
- **FR-M9-4** **Mandatory persistent disclaimer**, rendered on-screen and included in every API response from this module:
  > "This module is a simulation for analytical demonstration. It does not represent an official CPI revision or official NSO methodology."
- **FR-M9-5** Any CPI reference data used must display its **vintage and base year** (e.g. "CPI 2012-base series" vs "CPI 2024-base, HCES 2023-24 weights"). Mixing vintages silently is prohibited.

**Simulation formula (v1)**

```
Augmented = Base_CPI x (1 - w) + Airfare_Index x w        where w = airfare weight (default 2.5%)
```

**Acceptance criteria**
- The disclaimer cannot be dismissed or hidden.
- Changing `w` updates the result live, and the formula is shown alongside the result.

---

### M10 — Backtesting Lab `P0`

**Purpose.** Prove the index tracks reality.

**Requirements**

- **FR-M10-1** Ingest publicly available DGCA monthly average-fare data as a benchmark series.
- **FR-M10-2** Run an out-of-sample back-test over **at least 30 days** (target: 90 days where data allows).
- **FR-M10-3** Compute and display: **MAE, RMSE, MAPE, Pearson correlation, directional (trend) accuracy**.
- **FR-M10-4** Overlay our index against the DGCA benchmark on one chart, with a residual/error panel beneath.
- **FR-M10-5** Support back-test configuration: date range, route subset, estimator variant — so estimator choice can be justified empirically.

**Acceptance criteria**
- The lab reports metrics computed from stored series; no metric is ever hardcoded.
- Train/test split is explicit and out-of-sample; the split boundary is displayed on the chart.

---

### M11 — Forecasting Engine `P0`

**Requirements**

- **FR-M11-1** MVP models: seasonal moving average, exponential smoothing, seasonal baseline.
- **FR-M11-2** Advanced models: SARIMA, gradient boosting, time-series regression.
- **FR-M11-3** Forecast horizon: 14 days for route fares and the national index.
- **FR-M11-4** **Always output prediction intervals** (lower/upper bound). A point forecast must never be shown alone.
- **FR-M11-5** Display a model-comparison table (model -> MAPE on validation) and record which model version produced each stored forecast.
- **FR-M11-6** Output an interpretable "Expected Airfare Pressure" band (LOW / MEDIUM / HIGH) alongside the numeric range.

**Acceptance criteria**
- Model selection is justified by validation error, not asserted.
- Every stored forecast row carries `model_version`.

---

### M12 — Data Explorer `P1`

**Purpose.** Auditability.

- **FR-M12-1** Browse individual observations with columns: timestamp, origin, destination, airline, flight, departure date, lead days, fare class, base fare, tax, fee, total fare, source, quality score.
- **FR-M12-2** Filter by date, route, airline, OTA, fare class, lead time, source, quality band.
- **FR-M12-3** Toggle raw vs cleaned view, showing what the pipeline changed.
- **FR-M12-4** Export the current filtered view to CSV / JSON (capped and rate-limited).
- **FR-M12-5** Server-side pagination; no unbounded queries.

---

### M13 — API Portal `P0`

**Requirements**

- **FR-M13-1** Versioned REST endpoints under `/api/v1`:

| Endpoint | Returns |
|---|---|
| `GET /api/v1/index` | National + regional index series |
| `GET /api/v1/index/route/{route_code}` | Route index series (e.g. `DEL-BOM`) |
| `GET /api/v1/fares` | Filtered fare observations |
| `GET /api/v1/anomalies` | Detected anomalies |
| `GET /api/v1/forecast` | Forecasts with bounds |
| `GET /api/v1/routes` | Route master + weights |
| `GET /api/v1/airlines` | Airline master |
| `GET /api/v1/lead-time` | Lead-time curves and elasticity |
| `GET /api/v1/cpi-simulation` | CPI augmentation simulation |
| `GET /api/v1/backtest` | Back-test metrics and series |
| `GET /api/v1/data-quality` | Quality and collection health |

- **FR-M13-2** All responses JSON, with a consistent envelope: `{ data, meta, methodology_version, disclaimer? }`.
- **FR-M13-3** Support date filtering (`from`, `to`), route filtering, granularity (`daily|weekly|monthly`), pagination (`page`, `page_size`).
- **FR-M13-4** API-key authentication with scoped roles; per-key rate limiting with `X-RateLimit-*` headers.
- **FR-M13-5** Auto-generated OpenAPI 3.1 docs at `/api/docs`, plus an in-app portal page with copyable examples.
- **FR-M13-6** Deprecation policy: breaking changes require a new version path.

---

### M14 — Collection Engine Control `P1`

- **FR-M14-1** Per-source adapter status board: last run, records found / valid / failed, success rate, latency.
- **FR-M14-2** Scheduler view: next run per source, cron expressions, manual trigger (admin only).
- **FR-M14-3** Failure alerting and automatic source-fallback with a data-quality flag raised on the affected period.

---

## 6. Data collection requirements

- **FR-DC-1** Coverage target (Phase 1): **5 airlines, 3 OTAs, 10-15 routes, 5 lead-time windows**. Scale target: 100+ routes.
- **FR-DC-2** Source-adapter architecture — one adapter per source implementing a common interface, so a frontend change at one source cannot break the system.
- **FR-DC-3** Collection cadence: at least once daily per (route x lead-time window x source); more frequently for the top-weight routes.
- **FR-DC-4** Ethical safeguards are **hard requirements**: robots.txt awareness, per-source rate limits, response caching, scheduled off-peak collection, minimal request frequency, honouring terms of service, source attribution in the UI.
- **FR-DC-5** The system **must not** attempt to bypass CAPTCHAs, login walls or any access control. Where a source is inaccessible, it is marked unavailable and the fallback path is used.
- **FR-DC-6** Where a source blocks collection, the pipeline degrades gracefully: `SOURCE DOWN -> fallback source -> data-quality flag -> index continues`.

---

## 7. Data quality requirements

- **FR-DQ-1** Every observation receives a **quality score (0-100)** computed from: completeness, source reliability, timestamp validity, fare consistency, duplicate status, route validity, tax consistency, availability validity.
- **FR-DQ-2** Quality bands: HIGH CONFIDENCE (85+), MEDIUM (60-84), LOW (below 60).
- **FR-DQ-3** Only observations at or above a configurable threshold (default 60) enter index computation; the threshold is recorded with the methodology version.
- **FR-DQ-4** The cleaning pipeline is a fixed ordered sequence: schema validation -> normalisation -> deduplication -> missing-value handling -> outlier detection -> fare decomposition -> quality scoring.
- **FR-DQ-5** Raw observations are retained immutably; cleaning produces a derived record, never an in-place overwrite.

---

## 8. Non-functional requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-1 | Performance | p95 API latency under 400 ms for cached aggregates; under 1.5 s for cold analytical queries |
| NFR-2 | Performance | Dashboard first contentful paint under 1.5 s; fully interactive under 2.5 s |
| NFR-3 | Scale | Handle 5M+ fare observations without query degradation (partitioning + rollup tables) |
| NFR-4 | Availability | Dashboard and API remain functional when **all** external sources are down |
| NFR-5 | Security | API-key auth, RBAC (public / analyst / admin), rate limiting, encrypted secrets, no secrets in source |
| NFR-6 | Auditability | Every index value traceable to its input observations and methodology version |
| NFR-7 | Observability | Structured logging, per-source metrics, pipeline run records, health endpoints |
| NFR-8 | Reproducibility | Deterministic recomputation given the same inputs and methodology version |
| NFR-9 | Privacy | Zero personal data collected or stored, by design |
| NFR-10 | Portability | Full stack runs via `docker compose up` on a laptop |
| NFR-11 | Accessibility | WCAG 2.1 AA: contrast, keyboard navigation, screen-reader labels on charts |
| NFR-12 | Testing | 70%+ coverage on index, quality and anomaly logic; golden-file tests for index math |

---

## 9. Demo resilience requirements `P0`

The SIH demo must not depend on live scraping.

- **FR-DEMO-1** The system operates in three data modes: `LIVE` (fresh scrape), `CACHED` (recent stored observations), `REPLAY` (seeded historical dataset).
- **FR-DEMO-2** Mode is visible in the UI at all times; replayed or simulated data is **explicitly labelled**.
- **FR-DEMO-3** A seeded dataset covering the full demo path ships with the repository, loadable with one command.
- **FR-DEMO-4** Every hero feature is fully demonstrable with the network interface disabled.

---

## 10. User journey — the guided demo path

```
OPEN DASHBOARD
      |  India Airfare Index = live computed value
CLICK "TOP PRICE SURGE"
      |
OPEN DEL -> BOM ROUTE PAGE
      |  fare trend + expected baseline band
SEE LEAD-TIME CURVE   (T+45 ... T+1)
      |
SEE AIRLINE / OTA DIVERGENCE + FARE COMPOSITION
      |
SEE ANOMALY EXPLANATION  (expected vs observed + factor attribution)
      |
VIEW 14-DAY FORECAST  (with confidence interval)
      |
OPEN BACKTESTING LAB  (our index vs DGCA + error metrics)
      |
OPEN CPI AUGMENTATION SIMULATOR   <- closing wow
```

**Why the path is coherent:** one INR 8,000 observation on DEL-BOM simultaneously (a) enters the route price distribution feeding the national index, (b) populates the T+15 lead-time bucket, (c) is scored against the lead-time-aware baseline by the anomaly engine, (d) becomes training data for the forecaster, and (e) flows through the index into the CPI simulation. **One data point powers every analytical layer.**

---

## 11. Hero features (presentation priority)

| Rank | Feature | Question it answers |
|---|---|---|
| 1 | India Airfare Price Index | What is happening to airfare prices? |
| 2 | Anomaly & Surge Intelligence | Where are prices behaving abnormally, and why? |
| 3 | Lead-Time & Demand Intelligence | How does booking timing affect price? |
| 4 | CPI Augmentation Simulator | How can high-frequency airfare data support statistical analysis? |
| 5 | Backtesting & Forecasting | Does the system work, and what happens next? |

---

## 12. Success metrics

### 12.1 Product / statistical metrics

| Metric | Target |
|---|---|
| Index-DGCA correlation | 0.85 or higher |
| Index MAPE vs DGCA benchmark | 6% or lower |
| Directional (trend) accuracy | 85% or higher |
| Forecast MAPE (14-day horizon) | 10% or lower |
| Observation quality: HIGH-confidence share | 80% or higher |
| Route coverage completeness per collection day | 95%+ of active basket |
| Anomaly precision (manually reviewed sample) | 80% or higher |

### 12.2 System metrics

| Metric | Target |
|---|---|
| Daily observations collected | 20,000+ at Phase-3 scale |
| Pipeline end-to-end latency (scrape to index) | under 30 min |
| Scraper success rate per source | 90%+ |
| API uptime during demo window | 100% |

---

## 13. Release plan

| Phase | Scope | Exit criteria |
|---|---|---|
| **P1 — Foundation** | DB schema, route/airline/airport masters, first scraper adapters, cleaning pipeline | 5 airlines, 3 OTAs, 10-15 routes, 5 windows flowing into the DB |
| **P2 — Index** | Route weights, route index, national index, trend dashboard | A published, reproducible national index number |
| **P3 — Intelligence** | Lead-time analysis, anomaly detection, volatility, airline/OTA comparison | Anomalies detected with factor attribution |
| **P4 — Validation** | DGCA ingest, 30-day back-test, accuracy metrics | Back-test metrics displayed in the Lab |
| **P5 — Advanced** | Forecasting, event analysis, CPI simulator | 14-day forecast with intervals + CPI simulation live |
| **P6 — Production** | API hardening, Docker, auth, monitoring, tests, docs | `docker compose up` gives the full stack; API documented |

---

## 14. Risks and mitigations

| # | Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| R1 | Source blocks scraping during judging | Demo failure | High | Three-mode data strategy (LIVE/CACHED/REPLAY); seeded dataset; never depend on live scrape |
| R2 | Source frontend changes break an adapter | Data gaps | High | Adapter isolation; per-adapter contract tests; automatic fallback + quality flag |
| R3 | Thin data makes the index noisy | Weak statistical claim | Medium | Robust estimators; minimum-observation thresholds per route-period; renormalised weights |
| R4 | DGCA benchmark granularity mismatch (monthly vs daily) | Back-test invalid | Medium | Aggregate our daily index to monthly for comparison; state the alignment method explicitly |
| R5 | Judges read the CPI module as an official claim | Credibility damage | Medium | Non-dismissible disclaimer in UI and API; framing as simulation throughout |
| R6 | Scraper failure misread as a market surge | False anomaly | Medium | Dedicated scraper-anomaly detection (identical-value floods, distribution collapse) |
| R7 | Legal/ethical concern about scraping | Disqualification risk | Low | Documented ethical scraping policy; robots.txt; rate limits; no access-control bypass; source attribution |
| R8 | Scope overrun before deadline | Incomplete demo | High | Strict P0/P1/P2 priority; hero-feature-first build order |

---

## 15. Open questions

| # | Question | Owner | Needed by |
|---|---|---|---|
| Q1 | Which exact DGCA publication and vintage is the benchmark? | Data lead | Phase 4 |
| Q2 | Base period for the index (fixed calendar month vs rolling)? | Stats lead | Phase 2 |
| Q3 | Final basket size for the demo (15 vs 25 routes)? | Product lead | Phase 1 |
| Q4 | CPI reference dataset vintage to display (2012-base vs 2024-base)? | Stats lead | Phase 5 |
| Q5 | Which sources are confirmed accessible under their terms? | Eng lead | Phase 1 |

---

## 16. Glossary

| Term | Meaning |
|---|---|
| **Advance-purchase window / lead time** | Days between observation date and departure date (T+1 through T+45) |
| **Basket** | The fixed set of representative city-pairs used to construct the index |
| **CPI** | Consumer Price Index; current series is 2024-base with HCES 2023-24 weights, COICOP 2018 |
| **DGCA** | Directorate General of Civil Aviation — source of passenger traffic and benchmark fare data |
| **Fare composition** | Base fare + taxes + UDF + airport charges + convenience fee |
| **MoSPI / NSO** | Ministry of Statistics and Programme Implementation / National Statistical Office |
| **OTA** | Online Travel Aggregator (MakeMyTrip, Goibibo, Yatra, Cleartrip, EaseMyTrip, Ixigo) |
| **Quality score** | 0-100 confidence score attached to each fare observation |
| **Robust estimator** | Median / trimmed mean / weighted median — resistant to outliers |
| **UDF** | User Development Fee levied by airports |
