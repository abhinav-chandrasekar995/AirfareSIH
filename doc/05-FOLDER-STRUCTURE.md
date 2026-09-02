# Folder Structure Document
## INDIA AIRFARE INTELLIGENCE

| Field | Value |
|---|---|
| Document | Repository & Folder Structure |
| Version | 1.0 |
| Last updated | 2026-09-01 |
| Related docs | [PRD](01-PRD.md) · [Architecture](02-ARCHITECTURE.md) · [Design](03-DESIGN.md) · [Schema](04-BACKEND-SCHEMA.md) |

---

## 1. Repository layout (top level)

Monorepo, three deployable units (`frontend`, `backend`, `infra`) plus shared docs and seed data.

```
AirfareSIH/
├── doc/                          # This documentation set
│   ├── 01-PRD.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-DESIGN.md
│   ├── 04-BACKEND-SCHEMA.md
│   └── 05-FOLDER-STRUCTURE.md
│
├── frontend/                     # Next.js + React + TypeScript
├── backend/                      # FastAPI + Celery + analytics/ML
├── infra/                        # Docker, compose, deployment configs
├── scripts/                      # Cross-cutting dev/ops scripts
├── .github/
│   └── workflows/                # CI: lint, test, build, image publish
├── .env.example
├── docker-compose.yml
├── docker-compose.override.yml   # local dev overrides (hot reload)
├── Makefile                      # make dev / make seed / make test / make demo
├── README.md
└── LICENSE
```

---

## 2. Backend — `backend/`

```
backend/
├── app/
│   ├── main.py                        # FastAPI app factory, middleware wiring
│   ├── config.py                      # Pydantic Settings, env-driven
│   ├── dependencies.py                # shared FastAPI Depends() (auth, db session, pagination)
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py              # aggregates all v1 routers
│   │       ├── routers/
│   │       │   ├── index.py           # GET /index, /index/route/{code}, /index/methodology
│   │       │   ├── routes.py          # GET /routes
│   │       │   ├── airlines.py        # GET /airlines
│   │       │   ├── fares.py           # GET /fares  (Data Explorer backing)
│   │       │   ├── lead_time.py       # GET /lead-time
│   │       │   ├── anomalies.py       # GET /anomalies, /anomalies/{id}
│   │       │   ├── volatility.py      # GET /volatility
│   │       │   ├── divergence.py      # GET /divergence
│   │       │   ├── forecast.py        # GET /forecast
│   │       │   ├── backtest.py        # GET /backtest
│   │       │   ├── cpi_simulation.py  # GET/POST /cpi-simulation
│   │       │   ├── data_quality.py    # GET /data-quality
│   │       │   ├── events.py          # GET /events
│   │       │   └── admin.py           # POST /admin/collection/trigger, /admin/weights, audit-log
│   │       └── schemas/
│   │           ├── envelope.py        # shared { data, meta, methodology_version, disclaimer } model
│   │           ├── index.py
│   │           ├── fares.py
│   │           ├── lead_time.py
│   │           ├── anomalies.py
│   │           ├── forecast.py
│   │           ├── backtest.py
│   │           ├── cpi_simulation.py
│   │           └── common.py          # pagination, date-range, enums
│   │
│   ├── middleware/
│   │   ├── auth.py                    # API key resolution -> principal + role
│   │   ├── rate_limit.py              # Redis token bucket
│   │   ├── request_context.py         # request id, structured log binding
│   │   └── cpi_disclaimer.py          # injects the mandatory disclaimer (ADR-005)
│   │
│   ├── services/                      # orchestration layer; owns caching policy
│   │   ├── index_service.py
│   │   ├── route_service.py
│   │   ├── lead_time_service.py
│   │   ├── anomaly_service.py
│   │   ├── volatility_service.py
│   │   ├── divergence_service.py
│   │   ├── forecast_service.py
│   │   ├── backtest_service.py
│   │   ├── cpi_simulation_service.py
│   │   ├── data_quality_service.py
│   │   └── admin_service.py
│   │
│   ├── analytics/                     # PURE, no I/O — see ADR-001. Fully unit-testable.
│   │   ├── __init__.py
│   │   ├── estimators.py              # mean, median, trimmed_mean, weighted_median
│   │   ├── index_engine/
│   │   │   ├── route_index.py
│   │   │   ├── regional_index.py
│   │   │   ├── national_index.py      # Laspeyres-style weighted aggregation
│   │   │   └── weights.py             # renormalisation over observed routes
│   │   ├── lead_time/
│   │   │   ├── curve.py
│   │   │   ├── elasticity.py          # OLS ln(fare) ~ ln(lead_days)
│   │   │   └── premium.py             # last-minute premium calc
│   │   ├── volatility/
│   │   │   └── metrics.py             # stddev, CV, rolling volatility, banding
│   │   ├── anomaly/
│   │   │   ├── baseline.py            # expected-fare baseline model
│   │   │   ├── detectors/
│   │   │   │   ├── zscore.py
│   │   │   │   ├── iqr.py
│   │   │   │   ├── mad.py
│   │   │   │   └── isolation_forest.py
│   │   │   ├── attribution.py         # contributing-factor breakdown
│   │   │   └── scraper_anomaly.py     # FR-M5-6: distinguishes scraper vs market anomalies
│   │   ├── forecasting/
│   │   │   ├── baselines.py           # seasonal MA, exponential smoothing
│   │   │   ├── sarima_model.py
│   │   │   ├── gradient_boosting_model.py
│   │   │   ├── model_registry.py      # walk-forward validation + selection
│   │   │   └── intervals.py           # prediction interval computation
│   │   ├── backtest/
│   │   │   ├── alignment.py           # daily-index-to-monthly-DGCA alignment
│   │   │   └── metrics.py             # MAE, RMSE, MAPE, correlation, directional accuracy
│   │   └── cpi/
│   │       └── simulation.py          # Augmented = base*(1-w) + airfare*w
│   │
│   ├── pipeline/                      # Stage 2 — Clean (Celery `pipeline` queue)
│   │   ├── validate.py                # Pydantic schema validation of raw payloads
│   │   ├── normalise.py               # IATA/airline code mapping, timezone, currency
│   │   ├── deduplicate.py             # Redis lock + natural-key check
│   │   ├── impute.py                  # controlled missing-value handling
│   │   ├── outliers.py                # IQR/MAD flagging (never silent drop)
│   │   ├── decompose.py               # fare component consistency check
│   │   ├── quality_score.py           # 8-factor weighted scoring
│   │   └── pipeline_runner.py         # orchestrates the fixed 7-step chain
│   │
│   ├── collection/                    # Stage 1 — Collect
│   │   ├── orchestrator.py            # builds routes x windows x sources work matrix
│   │   ├── base_adapter.py            # BaseSourceAdapter — owns robots/rate-limit/audit (ADR-004)
│   │   ├── guards/
│   │   │   ├── robots_guard.py
│   │   │   ├── rate_limiter.py
│   │   │   ├── circuit_breaker.py
│   │   │   └── challenge_detector.py  # CAPTCHA/login-wall detection -> mark UNAVAILABLE
│   │   ├── transports/
│   │   │   ├── httpx_client.py
│   │   │   └── playwright_pool.py     # pooled browser contexts, session reuse
│   │   ├── adapters/
│   │   │   ├── airlines/
│   │   │   │   ├── indigo_adapter.py
│   │   │   │   ├── air_india_adapter.py
│   │   │   │   ├── air_india_express_adapter.py
│   │   │   │   ├── akasa_adapter.py
│   │   │   │   └── spicejet_adapter.py
│   │   │   └── otas/
│   │   │       ├── makemytrip_adapter.py
│   │   │       ├── goibibo_adapter.py
│   │   │       ├── yatra_adapter.py
│   │   │       ├── cleartrip_adapter.py
│   │   │       ├── easemytrip_adapter.py
│   │   │       └── ixigo_adapter.py
│   │   └── registry.py                # source_code -> adapter class lookup
│   │
│   ├── data_mode/
│   │   └── resolver.py                # DataModeResolver: LIVE / CACHED / REPLAY (Sec. 9, arch doc)
│   │
│   ├── db/
│   │   ├── base.py                    # SQLAlchemy declarative base, session factory
│   │   ├── session.py                 # async session dependency
│   │   ├── models/
│   │   │   ├── airport.py
│   │   │   ├── airline.py
│   │   │   ├── route.py
│   │   │   ├── route_weight.py
│   │   │   ├── source.py
│   │   │   ├── event.py
│   │   │   ├── dgca_benchmark.py
│   │   │   ├── cpi_reference.py
│   │   │   ├── fare_observation_raw.py
│   │   │   ├── fare_observation.py
│   │   │   ├── index_value.py
│   │   │   ├── leadtime_curve.py
│   │   │   ├── volatility_metric.py
│   │   │   ├── anomaly.py
│   │   │   ├── forecast.py
│   │   │   ├── backtest_run.py
│   │   │   ├── cpi_simulation.py
│   │   │   ├── scrape_run.py
│   │   │   ├── data_quality_flag.py
│   │   │   ├── api_key.py
│   │   │   ├── audit_log.py
│   │   │   └── methodology_version.py
│   │   └── repositories/              # ALL SQL lives here (Sec. 5.1, arch doc)
│   │       ├── index_repository.py
│   │       ├── fare_repository.py
│   │       ├── route_repository.py
│   │       ├── anomaly_repository.py
│   │       ├── forecast_repository.py
│   │       ├── backtest_repository.py
│   │       ├── cpi_repository.py
│   │       └── data_quality_repository.py
│   │
│   ├── tasks/                         # Celery task definitions (thin wrappers over the layers above)
│   │   ├── celery_app.py
│   │   ├── beat_schedule.py           # per-source cron, daily orchestration (Sec 8.2, arch doc)
│   │   ├── collect_tasks.py
│   │   ├── pipeline_tasks.py
│   │   ├── analytics_tasks.py
│   │   ├── ml_tasks.py
│   │   └── maintenance_tasks.py       # compression, retention, cache warm, reports
│   │
│   ├── core/
│   │   ├── security.py                # Argon2 hashing, API key verification
│   │   ├── cache.py                   # Redis cache-key helpers, TTL policy
│   │   ├── logging.py                 # structlog config
│   │   ├── telemetry.py               # OpenTelemetry setup
│   │   └── exceptions.py              # domain exceptions -> HTTP mapping
│   │
│   └── reports/
│       ├── generators/                # PDF/CSV report builders
│       └── templates/
│
├── alembic/
│   ├── env.py
│   └── versions/                      # one file per migration, reviewed like code
│
├── seeds/
│   ├── generate_seed.py               # deterministic, fixed-seed dataset builder
│   ├── fixtures/
│   │   ├── airports.csv
│   │   ├── airlines.csv
│   │   ├── routes.csv
│   │   ├── route_weights.csv
│   │   ├── events.csv
│   │   ├── dgca_benchmarks.csv
│   │   └── cpi_reference.csv
│   └── replay_dataset/                # the full REPLAY-mode demo dataset
│
├── tests/
│   ├── unit/
│   │   ├── analytics/                 # golden-file tests for index math (NFR-8)
│   │   │   ├── test_estimators.py
│   │   │   ├── test_index_engine.py
│   │   │   ├── test_lead_time.py
│   │   │   ├── test_anomaly_detectors.py
│   │   │   ├── test_forecasting.py
│   │   │   ├── test_backtest_metrics.py
│   │   │   └── test_cpi_simulation.py
│   │   ├── pipeline/
│   │   └── collection/
│   │       └── test_base_adapter_guards.py   # robots/rate-limit/challenge enforcement
│   ├── integration/
│   │   ├── test_api_index.py
│   │   ├── test_api_anomalies.py
│   │   ├── test_api_cpi_simulation.py         # asserts disclaimer always present
│   │   └── test_pipeline_end_to_end.py
│   ├── e2e/
│   │   └── test_demo_path_network_off.py      # FR-DEMO-4: network disabled, full journey works
│   ├── golden/                                # frozen expected outputs for index recomputation
│   └── conftest.py
│
├── pyproject.toml
├── poetry.lock                        # or requirements.txt / requirements-dev.txt
├── alembic.ini
├── Dockerfile
├── Dockerfile.worker
└── .env.example
```

### 2.1 Why `analytics/` sits where it does

`app/analytics/` has no sibling import from `app/db`, `app/api`, or `app/collection` (enforced by an `import-linter` contract in `pyproject.toml`, checked in CI). Everything above it (`services/`) loads data and passes plain DataFrames/dataclasses in; everything below it (`db/`) never appears in its call stack. This is ADR-001 made literal in the folder tree — you can point at the directory boundary and know the reproducibility guarantee holds.

---

## 3. Frontend — `frontend/`

```
frontend/
├── src/
│   ├── app/                           # Next.js App Router
│   │   ├── layout.tsx                 # root layout: theme provider, query client
│   │   ├── page.tsx                   # redirects to /dashboard
│   │   ├── globals.css                # imports tokens.css, Tailwind base
│   │   │
│   │   ├── (marketing)/
│   │   │   ├── layout.tsx
│   │   │   └── methodology/page.tsx   # static, SSG — public methodology explainer
│   │   │
│   │   └── (app)/
│   │       ├── layout.tsx             # sidebar + top bar shell, data-mode badge
│   │       ├── dashboard/page.tsx
│   │       ├── index/
│   │       │   ├── page.tsx           # national/regional index
│   │       │   └── methodology/page.tsx
│   │       ├── routes/
│   │       │   ├── page.tsx           # route list
│   │       │   └── [routeCode]/page.tsx
│   │       ├── anomalies/
│   │       │   ├── page.tsx
│   │       │   └── [anomalyId]/page.tsx
│   │       ├── lead-time/page.tsx
│   │       ├── cpi-simulator/page.tsx
│   │       ├── backtesting/page.tsx
│   │       ├── forecast/page.tsx
│   │       ├── data-explorer/page.tsx
│   │       ├── collection/page.tsx
│   │       ├── api-portal/
│   │       │   ├── page.tsx
│   │       │   └── keys/page.tsx
│   │       ├── reports/page.tsx
│   │       └── settings/page.tsx
│   │
│   ├── components/
│   │   ├── ui/                        # shadcn/ui primitives (button, input, tabs, dialog, ...)
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   └── DataModeBadge.tsx
│   │   ├── panels/
│   │   │   ├── PanelShell.tsx         # header + content + mandatory source footer
│   │   │   └── MethodologyPopover.tsx
│   │   ├── kpi/
│   │   │   ├── KpiCard.tsx
│   │   │   ├── HeroKpiCard.tsx
│   │   │   └── DeltaChip.tsx
│   │   ├── badges/
│   │   │   ├── SeverityBadge.tsx
│   │   │   └── QualityIndicator.tsx
│   │   ├── charts/
│   │   │   ├── IndexTrendChart.tsx
│   │   │   ├── FareTrendChart.tsx
│   │   │   ├── LeadTimeCurveChart.tsx
│   │   │   ├── ForecastChart.tsx      # TS requires lower/upper props — no bare point forecast
│   │   │   ├── BenchmarkOverlayChart.tsx
│   │   │   ├── ResidualChart.tsx
│   │   │   ├── PressureMap.tsx        # ECharts geo, offline India GeoJSON
│   │   │   ├── AirlineBoxPlot.tsx
│   │   │   ├── SourceSpreadChart.tsx
│   │   │   ├── FareCompositionBar.tsx
│   │   │   ├── AttributionBars.tsx
│   │   │   └── SensitivityChart.tsx
│   │   ├── tables/
│   │   │   ├── ObservationTable.tsx   # virtualised
│   │   │   ├── MoversList.tsx
│   │   │   └── ModelComparisonTable.tsx
│   │   ├── filters/
│   │   │   ├── FilterBar.tsx
│   │   │   └── FilterChips.tsx
│   │   ├── cpi/
│   │   │   ├── DisclaimerBanner.tsx
│   │   │   └── ScenarioSlider.tsx
│   │   ├── collection/
│   │   │   └── SourceStatusCard.tsx
│   │   └── api-portal/
│   │       ├── EndpointDoc.tsx
│   │       └── TryItPanel.tsx
│   │
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts              # generated from backend OpenAPI schema
│   │   │   └── hooks/                 # TanStack Query hooks per resource
│   │   │       ├── useIndex.ts
│   │   │       ├── useRoutes.ts
│   │   │       ├── useAnomalies.ts
│   │   │       ├── useLeadTime.ts
│   │   │       ├── useForecast.ts
│   │   │       ├── useBacktest.ts
│   │   │       └── useCpiSimulation.ts
│   │   ├── charts/
│   │   │   └── theme.ts               # ECharts/Plotly theme generated from tokens.css
│   │   ├── format/
│   │   │   ├── currency.ts            # Indian digit grouping
│   │   │   └── dates.ts               # IST formatting, ISO for exports
│   │   └── store/
│   │       └── uiStore.ts             # Zustand: filter panel, theme, chart prefs
│   │
│   ├── styles/
│   │   └── tokens.css                 # single source of truth (Sec. 2, design doc)
│   │
│   └── types/
│       └── api.generated.ts           # generated types from OpenAPI, never hand-edited
│
├── public/
│   ├── geo/india.json                 # bundled GeoJSON — offline pressure map
│   └── fonts/                         # self-hosted Inter, Inter Tight, JetBrains Mono
│
├── tests/
│   ├── unit/
│   ├── component/                     # Testing Library
│   └── e2e/                           # Playwright: guided demo path, network-off run
│
├── tailwind.config.ts                 # reads CSS variables from tokens.css
├── next.config.js
├── tsconfig.json
├── package.json
├── Dockerfile
└── .env.example
```

---

## 4. Infrastructure — `infra/`

```
infra/
├── docker/
│   ├── postgres/
│   │   └── init/                      # CREATE EXTENSION timescaledb; role setup
│   ├── nginx/
│   │   └── nginx.conf                 # reverse proxy, TLS, security headers
│   └── prometheus/
│       └── prometheus.yml             # scrape config (monitoring compose profile)
├── grafana/
│   └── dashboards/
│       ├── pipeline-health.json
│       └── api-performance.json
└── k8s/                                # optional post-hackathon production path
    ├── base/
    └── overlays/
        ├── staging/
        └── production/
```

---

## 5. Cross-cutting — `scripts/`

```
scripts/
├── dev_up.sh                          # docker compose up with dev overrides
├── seed_db.sh                         # wraps backend/seeds/generate_seed.py
├── run_backtest.sh                    # one-off backtest run from the CLI
├── check_migrations.sh                # CI: alembic upgrade head on a throwaway db
├── check_import_boundaries.sh         # CI: import-linter for analytics/ purity (ADR-001)
└── demo_network_off.sh                # brings the stack up with egress blocked, for FR-DEMO-4
```

---

## 6. Root-level files

```
.env.example          # documents every required env var name, no values
docker-compose.yml     # full stack: proxy, frontend, backend, worker, beat, db, redis
docker-compose.override.yml   # local hot-reload mounts, exposed debug ports
Makefile               # make dev | make seed | make test | make lint | make demo
.github/workflows/
  ci.yml                # lint + unit + integration tests, both frontend and backend
  import-boundaries.yml # enforces analytics/ purity
  e2e-network-off.yml   # runs the network-disabled demo-path test
```

---

## 7. Directory-to-requirement map

| Directory | Primary requirements satisfied |
|---|---|
| `backend/app/analytics/` | G3, NFR-8 — reproducible, testable statistical core (ADR-001) |
| `backend/app/collection/base_adapter.py` + `guards/` | FR-DC-4, FR-DC-5 — ethical collection is structural (ADR-004) |
| `backend/app/pipeline/` | FR-DQ-1..5 — the fixed seven-step cleaning chain |
| `backend/app/middleware/cpi_disclaimer.py` | FR-M9-4 — disclaimer cannot be omitted (ADR-005) |
| `backend/seeds/` + `data_mode/resolver.py` | FR-DEMO-1..4 — offline-safe demo |
| `backend/tests/golden/` | NFR-8 — recomputation produces identical values |
| `backend/tests/e2e/test_demo_path_network_off.py` | FR-DEMO-4, verified in CI |
| `frontend/src/components/panels/PanelShell.tsx` | D2 — every panel must declare its source (design doc §10) |
| `frontend/src/components/charts/ForecastChart.tsx` | FR-M11-4 — a point forecast cannot be rendered without bounds |
| `frontend/public/geo/india.json` | Offline pressure map for demo resilience |
| `infra/docker/postgres/init/` | TimescaleDB extension + hypertable bootstrap |
