# System Architecture
## INDIA AIRFARE INTELLIGENCE

| Field | Value |
|---|---|
| Document | Architecture Specification |
| Version | 1.0 |
| Stack | React (Next.js) · FastAPI (Python) · PostgreSQL + TimescaleDB · Redis · Celery · Docker |
| Last updated | 2026-09-01 |
| Related docs | [PRD](01-PRD.md) · [Design](03-DESIGN.md) · [Schema](04-BACKEND-SCHEMA.md) · [Folder Structure](05-FOLDER-STRUCTURE.md) |

---

## 1. Architectural principles

| # | Principle | Concrete consequence in this codebase |
|---|---|---|
| A1 | **Statistical correctness over visual effect** | Index math lives in a pure, dependency-free `analytics/` package with golden-file tests. The API is a thin wrapper over it. |
| A2 | **Raw data is immutable** | `fare_observations_raw` is append-only. Cleaning writes to `fare_observations`. You can always re-run the pipeline from raw. |
| A3 | **Adapters are isolated** | One source = one adapter class = one blast radius. A frontend change at MakeMyTrip cannot break IndiGo collection or the index. |
| A4 | **Everything is versioned** | `methodology_version`, `model_version`, `weight_set_version`, `adapter_version`. Any stored number can be traced to the code and config that produced it. |
| A5 | **Degrade, never fail** | Source down -> fallback -> quality flag -> index still publishes. The UI always renders from stored data. |
| A6 | **Separate the write path from the read path** | Scraping/cleaning/computation is async and batch. The API only reads pre-computed aggregates. Users never wait on a scrape. |
| A7 | **Ethical collection is architectural, not aspirational** | robots.txt checking, rate limiting and the "no access-control bypass" rule are enforced in the shared adapter base class, not left to individual adapters. |

---

## 2. Context view (C4 Level 1)

```
                    +---------------------------+
                    |     EXTERNAL SOURCES      |
                    |---------------------------|
                    | Airline sites (IndiGo,    |
                    | Air India, Akasa,         |
                    | SpiceJet, AI Express)     |
                    | OTAs (MMT, Goibibo,       |
                    | Yatra, Cleartrip, ...)    |
                    | DGCA traffic + fare data  |
                    | MoSPI CPI reference data  |
                    | Event / holiday calendar  |
                    +-------------+-------------+
                                  | (scheduled, rate-limited, robots-aware)
                                  v
      +-------------------------------------------------------------+
      |            INDIA AIRFARE INTELLIGENCE PLATFORM              |
      |  Collect -> Clean -> Measure -> Explain -> Validate ->       |
      |  Predict -> Augment                                         |
      +------+-------------------------+----------------------------+
             |                         |
             v                         v
   +---------------------+   +--------------------------+
   |  ANALYST / JUDGE    |   |  MACHINE CONSUMERS       |
   |  (Web dashboard)    |   |  (NSO / RBI / research)  |
   |  Chrome, desktop    |   |  REST API + API key      |
   +---------------------+   +--------------------------+
```

---

## 3. Container view (C4 Level 2)

```
                              INTERNET
                                 |
                        +--------v---------+
                        |  Nginx / Traefik |   TLS, routing, static
                        |  reverse proxy   |
                        +----+--------+----+
                             |        |
              /  (web)       |        |   /api/*  (json)
              v                       v
   +----------------------+   +---------------------------+
   |  FRONTEND            |   |  BACKEND API              |
   |  Next.js 14 (React)  |   |  FastAPI (ASGI, uvicorn)  |
   |  TypeScript          |-->|  Pydantic v2 schemas      |
   |  TanStack Query      |   |  SQLAlchemy 2.0 async     |
   |  ECharts + Plotly    |   |  API-key auth + RBAC      |
   |  Tailwind + shadcn   |   |  Rate limiter             |
   +----------------------+   +------+-------+------------+
                                     |       |
                        +------------+       +------------+
                        v                                 v
             +---------------------+          +------------------------+
             |  PostgreSQL 16      |          |  Redis 7               |
             |  + TimescaleDB      |          |  - response cache      |
             |  - raw observations |          |  - Celery broker       |
             |  - clean observations|         |  - rate-limit counters |
             |  - index values     |          |  - scrape dedupe locks |
             |  - anomalies        |          +------------------------+
             |  - forecasts        |                      ^
             |  - masters + audit  |                      |
             +----------+----------+                      |
                        ^                                 |
                        |                                 |
             +----------+---------------------------------+-----------+
             |            WORKER TIER (Celery)                        |
             |--------------------------------------------------------|
             |  celery-beat        scheduler (cron per source)        |
             |  worker:collect     runs source adapters               |
             |  worker:pipeline    clean / normalise / quality-score  |
             |  worker:analytics   index, lead-time, volatility       |
             |  worker:ml          anomaly detection, forecasting     |
             +------------------------+-------------------------------+
                                      |
                                      v
                         +-------------------------+
                         |  COLLECTION ENGINE      |
                         |  Playwright (JS pages)  |
                         |  httpx (JSON endpoints) |
                         |  Adapter registry       |
                         |  robots.txt guard       |
                         |  per-source rate limits |
                         +-------------------------+
```

### 3.1 Container responsibilities

| Container | Technology | Responsibility | Scales by |
|---|---|---|---|
| Reverse proxy | Nginx / Traefik | TLS, routing, gzip, static asset serving | Vertical |
| Frontend | Next.js 14, React 18, TypeScript | Server-rendered shell, client-side charting, routing | Stateless replicas |
| Backend API | FastAPI + uvicorn | Read-only analytical API, auth, rate limiting, OpenAPI | Stateless replicas |
| Database | PostgreSQL 16 + TimescaleDB | System of record; hypertables for time-series; continuous aggregates | Read replicas + partitioning |
| Cache/broker | Redis 7 | Response cache, Celery broker/result backend, rate-limit counters, distributed locks | Vertical / cluster |
| Workers | Celery | All write-path work: collection, cleaning, analytics, ML | Horizontal per queue |
| Scheduler | celery-beat | Cron triggers per source and per analytics job | Single instance (leader) |

---

## 4. The seven-stage pipeline

The entire product is one directional pipeline. Each stage has a defined input contract, output contract, and failure behaviour.

```
 [1] COLLECT      adapters -> raw payloads
       |
 [2] CLEAN        validate -> normalise -> dedupe -> impute -> outliers
       |                   -> decompose fare -> quality score
       |
 [3] MEASURE      route price measure -> route index -> regional -> national
       |
 [4] EXPLAIN      lead-time curve -> baseline -> anomaly + factor attribution
       |
 [5] VALIDATE     DGCA benchmark -> back-test -> MAE/RMSE/MAPE/corr/direction
       |
 [6] PREDICT      model selection -> forecast + prediction interval
       |
 [7] AUGMENT      CPI simulation (scenario-weighted, labelled)
       |
       v
    API + DASHBOARD + REPORTS
```

### 4.1 Stage 1 — Collect

**Component:** `collection/` (Celery `collect` queue)

```
        celery-beat (cron per source)
                  |
                  v
      +-----------------------------+
      |   ScrapingOrchestrator      |
      |  - builds the work matrix:  |
      |    routes x windows x srcs  |
      |  - applies robots.txt guard |
      |  - applies rate limiter     |
      |  - dispatches adapter tasks |
      +--------------+--------------+
                     |
   +--------+--------+--------+--------+--------+
   v        v        v        v        v        v
IndiGo   AirIndia  Akasa   SpiceJet  MMT    Goibibo   ... (adapters)
   \        |        |        |       |        /
    +-------+--------+---+----+-------+-------+
                         v
              raw payload + run metadata
                         v
              fare_observations_raw  (append-only)
              scrape_runs            (per-run audit)
```

**Adapter contract.** Every adapter subclasses `BaseSourceAdapter` and implements:

```python
class BaseSourceAdapter(ABC):
    source_code: str          # "indigo", "makemytrip", ...
    source_type: SourceType   # AIRLINE | OTA
    adapter_version: str      # bumped on any parsing change
    rate_limit: RateLimit     # requests/min, concurrency, backoff

    @abstractmethod
    async def fetch(self, query: FareQuery) -> RawPayload: ...

    @abstractmethod
    def parse(self, payload: RawPayload) -> list[RawFareObservation]: ...

    async def collect(self, query: FareQuery) -> CollectionResult:
        # provided by the base class - NOT overridable:
        #   robots.txt check -> rate limit acquire -> circuit breaker
        #   -> fetch -> parse -> schema-validate -> persist raw
        #   -> record scrape_run
```

**Why the base class owns `collect()`:** ethical safeguards (robots.txt, rate limits, no-bypass rule) and audit recording cannot be forgotten or opted out of by an individual adapter. This makes FR-DC-4 and FR-DC-5 structural.

**Resilience per source:**

```
 request -> [circuit breaker] -> [rate limiter] -> [retry w/ jitter]
                |                                       |
          open? skip source                       exhausted? mark
          mark UNAVAILABLE                        source DEGRADED
                |                                       |
                +------------> FALLBACK SOURCE ---------+
                                     |
                          raise data-quality flag
                          for the affected period
                                     |
                              index continues
```

**Two collection transports:**
- **`httpx`** for sources exposing a stable JSON endpoint — cheap, fast, low load.
- **Playwright** (headless Chromium) for JS-rendered pages — a pooled browser context per source, with session reuse to minimise request count.

Playwright is used **only** to render pages that a normal browser would render; it is never used to defeat a CAPTCHA, log in behind a wall, or evade a block. A source that responds with a challenge is marked `UNAVAILABLE` and skipped.

### 4.2 Stage 2 — Clean

**Component:** `pipeline/` (Celery `pipeline` queue). A fixed, ordered chain of pure functions:

```
RawFareObservation
      |
 [2.1] SCHEMA VALIDATION      Pydantic model; reject structurally invalid rows
      |
 [2.2] NORMALISATION          IATA codes uppercased, airline codes mapped,
      |                       currency -> INR, timestamps -> UTC,
      |                       fare class -> canonical enum, flight no. format
      |
 [2.3] DEDUPLICATION          natural key = (source, route, flight_no,
      |                       departure_datetime, fare_class, observed_at bucket)
      |                       Redis SETNX lock + DB unique constraint
      |
 [2.4] MISSING-VALUE HANDLING controlled imputation only where justified;
      |                       every imputed field recorded in `imputed_fields`
      |
 [2.5] OUTLIER DETECTION      IQR + MAD within (route, lead-bucket) group;
      |                       outliers are FLAGGED, never silently dropped
      |
 [2.6] FARE DECOMPOSITION     base + taxes + UDF + airport charges
      |                       + convenience fee == total (tolerance-checked)
      |
 [2.7] QUALITY SCORING        8 weighted factors -> 0-100 -> band
      |
      v
 fare_observations (clean, indexed, ready for analytics)
```

**Quality score model:**

```
score = 100 x SUM_i ( w_i x f_i )        where SUM_i w_i = 1

f_1 completeness         all required fields present
f_2 source_reliability   rolling success/consistency of that source
f_3 timestamp_validity   observed_at <= now, departure > observed_at
f_4 fare_consistency     total within plausible band for the route
f_5 duplicate_status     unique vs near-duplicate
f_6 route_validity       route is in the active basket, airports exist
f_7 tax_consistency      components sum to total within tolerance
f_8 availability_validity seats-available field sane / present
```

Bands: `HIGH >= 85`, `MEDIUM 60-84`, `LOW < 60`. Only `score >= quality_threshold` (default 60) enters index computation, and the threshold is stamped into the methodology version.

### 4.3 Stage 3 — Measure (the Index Engine)

**Component:** `analytics/index/` — pure Python + NumPy/Pandas, no I/O, fully unit-testable.

```
 fare_observations (quality-filtered)
              |
   group by (route, period)
              |
   +----------v-----------+
   |  ROBUST ESTIMATOR    |   computes ALL of:
   |                      |   mean, median, trimmed mean (10%),
   |                      |   weighted median
   |  configured estimator|   -> P(r,t) stored + all variants stored
   +----------+-----------+      for the estimator-comparison view
              |
      P(r,t) / P(r,base) x 100  ->  ROUTE INDEX  I(r,t)
              |
   +----------v-----------+
   |  WEIGHT APPLICATION  |   w(r) from DGCA passenger traffic
   |  weight_set_version  |   renormalise over observed routes
   +----------+-----------+
              |
      +-------+--------+---------------+
      v                v               v
 REGIONAL INDEX   NATIONAL INDEX   AIRLINE INDEX
      \                |               /
       +---------------v--------------+
                  index_values
        (date, level, scope, value, weight,
         estimator, methodology_version, notes)
```

**Minimum-observation rule.** A route-period with fewer than `min_observations` (default 5) valid observations is excluded from the index and its weight renormalised, with the exclusion written to `index_values.notes` so the omission is visible rather than silent.

### 4.4 Stage 4 — Explain (Lead-Time + Anomaly)

```
        fare_observations
                |
    +-----------+------------+
    v                        v
LEAD-TIME ENGINE       CONTEXT FEATURES
 buckets T+1/7/15/      day-of-week, month,
 30/45 per route        event proximity (calendar),
 -> curve               seat availability, season
 -> elasticity (OLS)          |
 -> last-min premium          |
    |                         |
    +-----------+-------------+
                v
     EXPECTED FARE BASELINE
     E[fare | route, lead_bucket, dow, season, event]
                |
                v
        +---------------------+
        |  ANOMALY DETECTORS  |
        |  z-score | IQR |    |   consensus / voting:
        |  MAD | IsolationF.  |   record which detectors fired
        +----------+----------+
                   |
          deviation = (observed - expected) / expected
                   |
          severity: LOW / MED / HIGH / CRITICAL
                   |
        +----------v-----------+
        | FACTOR ATTRIBUTION   |   contributions normalised to 100%,
        | (model-based, and    |   labelled "model-based attribution"
        |  labelled as such)   |   in both UI and API
        +----------+-----------+
                   |
                anomalies
```

**Scraper-anomaly separation (FR-M5-6).** Before a market anomaly is raised, the batch passes a *source-sanity* check: identical-value floods, collapsed variance, impossible tax ratios, or a sudden distribution shift confined to one source route to the **data-quality** alert path instead of the market-anomaly path. This prevents "our scraper broke" from being presented as "prices surged".

### 4.5 Stage 5 — Validate (Backtesting Lab)

```
 our index (daily)          DGCA benchmark (monthly)
        |                             |
   aggregate to monthly               |
   (documented alignment method)      |
        +--------------+--------------+
                       v
              ALIGNED SERIES PAIR
                       |
          explicit train / test split
          (out-of-sample test window >= 30 days)
                       |
        +--------------+---------------+
        v              v               v
     MAE / RMSE     MAPE / corr    directional accuracy
        \              |               /
         +-------------v--------------+
                 backtest_runs
         (config, metrics, split boundary,
          estimator variant, run timestamp)
```

The lab is parameterised by estimator variant so the choice of median vs trimmed mean vs weighted median is settled **empirically and visibly**, satisfying the "choose methodology based on robustness" requirement.

### 4.6 Stage 6 — Predict (Forecasting Engine)

```
 historical index / route series
              |
    feature build (lags, rolling stats, dow,
    month, event flags, lead-time context)
              |
   +----------v-----------+
   |   MODEL REGISTRY     |
   |  baseline: seasonal MA, exp. smoothing
   |  advanced: SARIMA, gradient boosting, TS regression
   +----------+-----------+
              |
     walk-forward validation -> MAPE per model
              |
     select best by validation error (never asserted)
              |
     forecast horizon = 14 days
     + prediction interval (lower / upper)
              |
              v
        forecasts  (model_version stamped)
        + pressure band LOW / MEDIUM / HIGH
```

A point forecast is never emitted without bounds — enforced at the Pydantic response-model level, so it cannot be bypassed by a careless endpoint.

### 4.7 Stage 7 — Augment (CPI Simulator)

```
  cpi_reference (vintage + base year explicit)
              +
      index_values (national airfare index)
              |
       scenario weight w  (user-adjustable, default 2.5%)
              |
   Augmented = Base_CPI x (1 - w) + Airfare_Index x w
              |
              v
       cpi_simulations  (scenario, inputs, result)
              |
     ALWAYS accompanied by the disclaimer string,
     injected by a response middleware so it cannot
     be omitted from any response of this module.
```

---

## 5. Backend application architecture (FastAPI)

### 5.1 Layering

```
   HTTP
     |
 [ROUTERS]        api/v1/routers/*.py
     |            thin: parse params -> call service -> return schema
     |            no business logic, no SQL
     v
 [SCHEMAS]        Pydantic v2 request/response models
     |            validation + OpenAPI generation + envelope
     v
 [SERVICES]       services/*.py
     |            orchestration, caching policy, permission checks
     v
 [ANALYTICS]      analytics/*   PURE functions: index math, lead-time,
     |            anomaly scoring, forecasting, CPI simulation.
     |            No DB, no HTTP, no globals -> trivially testable.
     v
 [REPOSITORIES]   db/repositories/*.py
     |            all SQL lives here; returns domain objects
     v
 [MODELS]         db/models/*.py   SQLAlchemy 2.0 ORM
     v
 PostgreSQL
```

**The rule that keeps this honest:** `analytics/` may not import from `db/`, `api/`, or `collection/`. It receives DataFrames/dataclasses and returns DataFrames/dataclasses. This is what makes the index reproducible and golden-file testable, and it is enforced by an import-linter rule in CI.

### 5.2 Request lifecycle

```
Client
  |  GET /api/v1/index?level=national&from=..&to=..&granularity=daily
  v
[Middleware: request id -> structured log context]
[Middleware: API key auth -> principal + role]
[Middleware: rate limiter (Redis token bucket per key)]
[Middleware: disclaimer injector (CPI module only)]
  v
Router  -> validate query params (Pydantic)
  v
Service -> cache key = hash(endpoint + params + methodology_version)
  |         Redis GET -> HIT? return
  |         MISS ->
  v
Repository -> SELECT from index_values / continuous aggregate
  v
Service -> shape response envelope, attach meta + methodology_version
  |         Redis SETEX (TTL by granularity: daily=1h, monthly=24h)
  v
Response { data, meta, methodology_version, disclaimer? }
```

**Cache invalidation:** every analytics job that writes new `index_values` publishes a Redis invalidation event keyed by `(level, scope)`. Cache keys embed `methodology_version`, so a methodology bump invalidates everything derived from it automatically.

### 5.3 Response envelope

```json
{
  "data": [ { "date": "2026-08-31", "level": "national", "index_value": 127.4 } ],
  "meta": {
    "count": 1,
    "page": 1,
    "page_size": 100,
    "granularity": "daily",
    "data_mode": "LIVE",
    "generated_at": "2026-09-01T04:12:00Z",
    "sources_included": ["indigo", "airindia", "makemytrip"],
    "quality_threshold": 60
  },
  "methodology_version": "idx-1.2.0",
  "disclaimer": null
}
```

`data_mode` (`LIVE` / `CACHED` / `REPLAY`) is present on every response so the frontend can render the demo-resilience badge truthfully without guessing.

### 5.4 Authentication and authorisation

| Role | Scope |
|---|---|
| `public` | Read national/regional index, routes, airlines. Heavily rate-limited. |
| `analyst` | All read endpoints including raw observation export and back-test configuration. |
| `admin` | Trigger collection runs, edit weights, publish methodology versions, manage keys. |

API keys are stored hashed (Argon2). The key's role, rate limit, and quota live in `api_keys`. Every privileged action writes to `audit_log`.

---

## 6. Frontend architecture (Next.js + React)

### 6.1 Structure

```
 Next.js App Router
   |
   +-- (marketing)  landing / methodology (static, SSG)
   +-- (app)        authenticated dashboard shell
         |
         +-- layout: sidebar nav + top bar (data-mode badge, freshness)
         |
         +-- /dashboard          KPI cards, index trend, movers, pressure map, insights
         +-- /index              national / regional / route / airline + methodology
         +-- /routes             list -> /routes/[code] detail
         +-- /anomalies          feed -> /anomalies/[id] explanation
         +-- /lead-time          curves, elasticity, premium
         +-- /cpi-simulator      scenario controls + persistent disclaimer
         +-- /backtesting        DGCA overlay, metrics, residuals
         +-- /forecast           horizon chart with intervals, model comparison
         +-- /data-explorer      virtualised table, filters, export
         +-- /collection         adapter health, scheduler, run history
         +-- /api-portal         endpoint docs, key management, examples
         +-- /reports            generated PDF/CSV reports
         +-- /settings           thresholds, preferences
```

### 6.2 Data layer

- **TanStack Query** for all server state: caching, background refetch, stale-while-revalidate.
- A single generated **API client** from the backend's OpenAPI schema, so frontend types cannot drift from backend contracts.
- **Zustand** for the small amount of genuine client state (filter panel state, chart preferences, theme).
- No client-side statistics. If a number appears on screen, the backend computed it. This guarantees the UI and the API can never disagree.

### 6.3 Charting

| Need | Library | Why |
|---|---|---|
| Time-series, candlestick-style ranges, dense financial charts | **Apache ECharts** | Handles large series, brushing, dataZoom, good performance |
| India pressure map (geo choropleth / route arcs) | **ECharts geo** with a bundled India GeoJSON | No external tile dependency; works offline for the demo |
| Statistical panels (distributions, residuals, box plots) | **Plotly.js** | Best-in-class statistical chart types out of the box |

All chart theming comes from the design tokens defined in [03-DESIGN.md](03-DESIGN.md), so charts and UI share one palette.

### 6.4 Rendering strategy

| Page type | Strategy | Reason |
|---|---|---|
| Landing, methodology | SSG | Static, cacheable, fast first impression |
| Dashboard, index, routes | SSR shell + client-side data fetch | Fast paint; charts hydrate with live data |
| Data Explorer | Client-side with server pagination | Table is interaction-heavy |
| Reports | Server-generated | PDF rendering server-side |

---

## 7. Data architecture

### 7.1 Storage tiers

```
 TIER 0  RAW            fare_observations_raw    append-only, JSONB payload,
                                                 retained for full reprocessing
 TIER 1  CLEAN          fare_observations        typed, quality-scored,
                                                 TimescaleDB hypertable
                                                 partitioned by observed_at
 TIER 2  AGGREGATES     continuous aggregates    route-day, route-leadbucket-day,
                                                 airline-day, source-day
 TIER 3  DERIVED        index_values,            the published statistical products
                        anomalies, forecasts,
                        volatility_metrics,
                        leadtime_curves
 TIER 4  REFERENCE      airports, routes,        slow-moving masters + external
                        airlines, sources,       benchmarks
                        route_weights,
                        dgca_benchmarks,
                        cpi_reference, events
 TIER 5  OPERATIONAL    scrape_runs, api_keys,   audit and control plane
                        audit_log, data_quality_flags
```

### 7.2 Why TimescaleDB

`fare_observations` is a classic time-series: high insert rate, append-mostly, always queried by time range plus a dimension (route/airline/source). TimescaleDB gives us, inside plain PostgreSQL:

- **Hypertable partitioning** by `observed_at` — queries prune to relevant chunks automatically.
- **Continuous aggregates** — route-day and route-leadbucket-day rollups refresh incrementally, so the dashboard reads a materialised view instead of scanning millions of rows. This is what makes NFR-1 and NFR-3 achievable.
- **Compression** on chunks older than 30 days.
- **Retention policies** on raw payloads.

It is a PostgreSQL extension, so there is no second database to operate and every ordinary SQL feature, foreign key and migration tool still applies.

### 7.3 Data flow of one observation

```
 One observation: DEL->BOM, IndiGo 6E-2134, dep 15 Sep,
 observed 30 Aug, lead 16d, total INR 6,800, source MakeMyTrip

  fare_observations_raw  (immutable JSONB + metadata)
            |
      clean pipeline -> quality score 94 (HIGH)
            |
  fare_observations  (typed row)
            |
   +--------+--------+--------+---------+---------+
   v        v        v        v         v         v
 route-  lead-    airline  OTA       anomaly   forecast
 day agg bucket   compare  compare   baseline  training
   |     agg        |        |         |         |
   v      v         v        v         v         v
 DEL-BOM  T+15    IndiGo   MMT vs   expected  next-14d
 index    curve   index    direct   vs actual  model
   |
   v
 NATIONAL INDEX -> CPI SIMULATION
```

This is the architectural claim in one picture: **a single observation is written once and read by six analytical layers.** Nothing is scraped twice for a different feature.

---

## 8. Asynchronous processing

### 8.1 Queue topology

| Queue | Worker concurrency | Tasks | Schedule |
|---|---|---|---|
| `collect` | High (I/O bound) | One task per (source, route, window) | Per-source cron, staggered off-peak |
| `pipeline` | Medium (CPU) | Clean + score batches of raw rows | Triggered on collection completion |
| `analytics` | Low (CPU heavy) | Index computation, lead-time, volatility | Daily after pipeline drain; on-demand |
| `ml` | Low | Anomaly detection, forecast training/inference | Daily; anomaly on each pipeline batch |
| `maintenance` | Low | Compression, retention, cache warm, report generation | Nightly |

### 8.2 Daily orchestration

```
 02:00  collect     staggered per source, respecting rate limits
   |
 04:00  pipeline    clean/score everything collected since last run
   |
 05:00  analytics   route measures -> route index -> regional -> national
   |                lead-time curves, volatility, divergence
   |
 05:30  ml          baseline refresh -> anomaly detection -> attribution
   |                forecast retrain (weekly) / inference (daily)
   |
 06:00  validate    incremental back-test refresh when new DGCA data exists
   |
 06:15  maintenance cache warm, continuous-aggregate refresh, report build
   |
 06:30  READY       dashboard and API serve the new vintage
```

Each stage records a run row; a failed stage does not block the next stage from operating on the last good vintage — the dashboard degrades to the previous day's index with a freshness warning rather than showing nothing.

### 8.3 Idempotency

Every task is idempotent and keyed:
- Collection tasks take a Redis lock on `(source, route, window, date)`.
- Cleaning is keyed on the raw row id; re-running overwrites the same derived row.
- Index computation is keyed on `(date, level, scope, methodology_version)` with an upsert.

Consequence: any task can be safely retried, and the whole pipeline can be replayed from raw at any time to reproduce a historical index.

---

## 9. Demo-resilience architecture

This is a first-class architectural concern, not an afterthought.

```
                    DataModeResolver (backend, per request)
                                |
        +-----------------------+-----------------------+
        |                       |                       |
      LIVE                   CACHED                  REPLAY
 fresh scrape within     stored observations     seeded historical
 the freshness SLA       older than SLA          dataset, fixed
        |                       |                       |
        +-----------+-----------+-----------+-----------+
                    |                       |
              data_mode field         UI badge rendered
              on every response       from that field
```

- **Seed dataset.** `backend/seeds/` ships a reproducible dataset covering the complete demo path (DEL-BOM surge, all five lead-time windows, a DGCA-comparable stretch, CPI reference rows). Loaded with `make seed`.
- **Determinism.** The seed is generated by a script with a fixed random seed, so the demo shows the same numbers every time it is loaded.
- **Honest labelling.** Replayed and simulated data are labelled in the UI. The architecture makes this automatic (the badge reads `meta.data_mode`) rather than depending on someone remembering to say it.
- **Network-off test.** CI runs an end-to-end test with outbound network blocked; the dashboard and all P0 endpoints must still pass.

---

## 10. Security architecture

| Layer | Control |
|---|---|
| Transport | TLS terminated at the proxy; HSTS |
| Authentication | API keys, Argon2-hashed at rest, prefix-indexed for lookup |
| Authorisation | RBAC (`public` / `analyst` / `admin`) enforced as a FastAPI dependency on every router |
| Rate limiting | Redis token bucket per key and per IP; `X-RateLimit-*` headers on all responses |
| Input validation | Pydantic v2 on every request; no raw string interpolation into SQL |
| SQL | SQLAlchemy parameterised queries exclusively; repositories are the only SQL surface |
| Secrets | Environment-injected, never committed; `.env.example` documents names only |
| Audit | `audit_log` records every admin action, weight change and methodology publish |
| Privacy | No personal data is collected, so there is no PII surface to protect |
| Dependencies | Pinned versions, `pip-audit` / `npm audit` in CI |
| Headers | CSP, X-Content-Type-Options, Referrer-Policy set at the proxy |

---

## 11. Ethical collection architecture

Because this is an evaluated dimension of the problem statement, the safeguards are placed where they cannot be skipped.

```
 Adapter.collect()   <- final, provided by BaseSourceAdapter
        |
   [1] RobotsGuard          fetch + cache robots.txt per host;
        |                   disallowed path -> abort, log, mark SKIPPED
   [2] RateLimiter          per-source token bucket in Redis, shared
        |                   across all workers (not per-process)
   [3] CircuitBreaker       consecutive failures -> open circuit, back off
        |
   [4] ResponseCache        identical query within TTL -> serve cached,
        |                   do not re-request the source
   [5] fetch()              adapter-specific transport
        |
   [6] ChallengeDetector    CAPTCHA / login wall / block page detected
        |                   -> mark source UNAVAILABLE, DO NOT retry,
        |                      DO NOT attempt to solve or evade
   [7] persist + attribute  store source attribution with every observation
```

Explicitly out of scope by design: CAPTCHA solving, credential-based login to gated fare inventory, proxy rotation for evasion, ignoring `Retry-After`, or any technique whose purpose is to defeat an access control. Where a source cannot be collected ethically, it is not collected — and the index reports reduced coverage rather than silently substituting.

---

## 12. Observability

| Signal | Implementation |
|---|---|
| Logs | `structlog` JSON to stdout; request id propagated from API into Celery tasks |
| Metrics | Prometheus endpoint: per-source success rate, records/run, pipeline latency, index freshness, API p95, cache hit rate |
| Traces | OpenTelemetry spans across API -> service -> repository and across Celery task chains |
| Health | `/health` (liveness), `/health/ready` (DB + Redis + last-successful-vintage age) |
| Dashboards | Grafana (optional in compose profile `monitoring`) |
| Data-quality alerts | `data_quality_flags` rows surfaced in the Collection Engine UI |

Key operational metric: **index freshness** — the age of the most recent published `index_values` row. If it exceeds the SLA, the UI shows a stale-data warning automatically.

---

## 13. Deployment architecture

### 13.1 Local / demo (docker compose)

```
 docker compose up
   proxy         nginx           :80
   frontend      next.js         :3000
   backend       fastapi         :8000
   worker        celery x2       (collect, pipeline+analytics+ml)
   beat          celery-beat
   db            postgres+timescale :5432
   redis         redis           :6379
   [profile monitoring] prometheus + grafana
```

One command brings up the entire platform on a laptop, which is the practical requirement for hackathon judging (NFR-10).

### 13.2 Production shape

```
                        INTERNET
                            |
                     +------v-------+
                     | LOAD BALANCER|  TLS, WAF, rate limit
                     +---+------+---+
                         |      |
                +--------v--+  +v-----------+
                | FRONTEND  |  |  FASTAPI   |  N stateless replicas
                | replicas  |  |  replicas  |
                +-----------+  +-----+------+
                                     |
                    +----------------+----------------+
                    v                v                v
             +-------------+  +-------------+  +--------------+
             | PostgreSQL  |  |   Redis     |  |   WORKERS    |
             | primary     |  |  cache +    |  |  collect     |
             |  + replica  |  |  broker     |  |  pipeline    |
             | (Timescale) |  |             |  |  analytics   |
             +-------------+  +-------------+  |  ml          |
                                               +------+-------+
                                                      |
                                          +-----------v-----------+
                                          |   COLLECTION ENGINE   |
                                          | Playwright pool +     |
                                          | httpx clients         |
                                          +-----------+-----------+
                                                      |
                                    +-----------------+-----------------+
                                    v                 v                 v
                                AIRLINES            OTAs        DGCA / MoSPI data
```

Scaling levers, in the order you would actually pull them:
1. Add `collect` workers (I/O bound) as route coverage grows.
2. Add API replicas behind the LB (stateless).
3. Add a read replica and point analytical reads at it.
4. Increase continuous-aggregate coverage to move more work off the hot path.
5. Compress and tier older chunks.

---

## 14. Technology decisions and rationale

| Decision | Choice | Rationale | Considered instead |
|---|---|---|---|
| Backend language | **Python** | The entire value chain is statistics and ML: Pandas, NumPy, SciPy, statsmodels, scikit-learn, Prophet-style models. Same language for API, pipeline and models means no serialisation boundary. | Node (would force a second Python service anyway) |
| API framework | **FastAPI** | Async, Pydantic validation, automatic OpenAPI (which generates the frontend client), excellent performance | Django REST (heavier), Flask (less typed) |
| Frontend | **Next.js + React + TypeScript** | Routing, SSR for fast paint, huge charting ecosystem, types shared via generated client | SPA-only React (slower first paint) |
| Charts | **ECharts + Plotly** | ECharts for dense financial time-series and offline geo maps; Plotly for statistical panels | Recharts (too limited for this density), D3 (too much hand-built work) |
| Database | **PostgreSQL 16 + TimescaleDB** | Relational integrity for masters + time-series performance for observations, in one system | MongoDB (loses joins/constraints), InfluxDB (loses relational masters) |
| Cache/broker | **Redis** | One component serves cache, Celery broker, rate limiter and locks | RabbitMQ + separate cache (more moving parts) |
| Task queue | **Celery + beat** | Mature, multiple queues, retries, scheduling | APScheduler (in-process, doesn't scale out), Airflow (operationally heavy for this) |
| Scraping | **Playwright + httpx** | Playwright renders JS pages and manages sessions; httpx is cheap where JSON endpoints exist | Selenium (slower), Scrapy alone (weak on JS rendering) |
| Migrations | **Alembic** | Standard with SQLAlchemy; versioned, reviewable schema history | Hand-written SQL (unreviewable drift) |
| Containers | **Docker + compose** | One-command demo bring-up; identical local and prod images | Bare-metal setup (fragile on judging day) |

---

## 15. Key architectural decision records

### ADR-001 — Analytics is a pure package with no I/O
**Decision.** `analytics/` may not import `db/`, `api/`, or `collection/`; CI enforces it with import-linter.
**Why.** Index reproducibility (NFR-8) and golden-file testing require that index math be a deterministic function of its inputs. Mixing in database access makes the math untestable and unreproducible.
**Cost.** Services must load data and pass DataFrames in. Accepted.

### ADR-002 — Raw observations are immutable and retained
**Decision.** `fare_observations_raw` is append-only; cleaning writes a separate row.
**Why.** Methodology will change during the build. Retaining raw means any historical index can be recomputed under a new methodology without re-scraping — and any judge question about "what if you used the median instead" is answerable in minutes.
**Cost.** Storage. Mitigated by TimescaleDB compression and a retention policy on payload blobs.

### ADR-003 — The API never triggers a scrape
**Decision.** All collection is scheduled and asynchronous; the read path only serves stored data.
**Why.** A user request must never depend on a third-party site being up. This is what makes NFR-4 and the demo-resilience requirement structurally true rather than hopeful.

### ADR-004 — Ethical safeguards live in the adapter base class
**Decision.** robots.txt checking, rate limiting, challenge detection and audit recording are in `BaseSourceAdapter.collect()`, which subclasses do not override.
**Why.** Compliance that depends on each contributor remembering will eventually fail. Making it structural means an adapter cannot be written that skips it.

### ADR-005 — The CPI disclaimer is injected by middleware
**Decision.** A response middleware attaches the disclaimer to every CPI-module response; the frontend renders it non-dismissibly.
**Why.** Misreading the simulator as an official CPI claim is the single largest credibility risk (R5). Making the disclaimer structural removes the possibility of an endpoint shipping without it.

### ADR-006 — Store every estimator variant, not just the chosen one
**Decision.** Route price measures persist mean, median, trimmed mean and weighted median alongside the configured estimator.
**Why.** The problem statement asks for methodology chosen on empirical robustness. Storing all variants makes the Backtesting Lab able to compare them retroactively, turning an assertion into a demonstration.
**Cost.** Four numeric columns per route-period. Negligible.

---

## 16. Architecture-to-requirement traceability

| Requirement | Architectural mechanism |
|---|---|
| Multiple advance-purchase windows | Work matrix `routes x {T+1,7,15,30,45} x sources` in the orchestrator; `lead_days` + `lead_bucket` columns; lead-time continuous aggregate |
| JS-rendered pages, session management | Playwright pool with per-source persistent contexts |
| Ethical scraping / anti-bot handling | `BaseSourceAdapter` guard chain; challenge detection marks UNAVAILABLE rather than evading |
| Data cleaning and normalisation | Fixed seven-step pipeline (Section 4.2) with per-step audit |
| Fare component separation | `base_fare`, `taxes`, `udf`, `airport_charges`, `convenience_fee`, `total_fare` + tax-consistency quality factor |
| Representative city-pairs from DGCA traffic | `routes` + versioned `route_weights` sourced from DGCA passenger data |
| Index construction and visualisation | Pure `analytics/index/` engine -> `index_values` -> ECharts dashboard |
| API for NSO/RBI consumption | Versioned FastAPI routers, API keys, rate limits, OpenAPI, stable envelope |
| 30-day back-test vs DGCA | `dgca_benchmarks` + Backtesting Lab with explicit out-of-sample split |
| Robustness of statistics | All four estimators stored; empirical comparison in the Lab |
| Resilience when a source fails | Circuit breaker -> fallback -> data-quality flag -> index continues |
| Demo without live network | `DataModeResolver` + seeded dataset + network-off CI test |
