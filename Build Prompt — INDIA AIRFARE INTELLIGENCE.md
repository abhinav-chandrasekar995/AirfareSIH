# Build Prompt — INDIA AIRFARE INTELLIGENCE

## Project Overview

Build a production-quality, full-stack web application called:

# INDIA AIRFARE INTELLIGENCE
### Real-Time Airfare Price Index & CPI Augmentation Platform

This must be designed as a **financial, statistical, and policy intelligence platform for India's domestic aviation market**.

Do **NOT** design it as a flight booking website.

The platform should transform fragmented airfare observations into:

- National Airfare Price Index
- Regional Airfare Indices
- Route-level intelligence
- Lead-time fare analysis
- Anomaly and surge detection
- Event and seasonal intelligence
- Airfare volatility analysis
- Airline and OTA price divergence analysis
- Forecasting
- DGCA benchmark backtesting
- CPI augmentation simulation
- Data-quality monitoring
- Collection engine monitoring
- API access and documentation

The product philosophy must be visible throughout the application:

> **Collect → Clean → Measure → Explain → Validate → Predict → Augment**

---

# 1. REQUIRED TECH STACK

## Frontend

Use:

- Next.js 14+ with App Router
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- Zustand for lightweight UI state
- ECharts and/or Plotly for advanced statistical visualisations

## Backend

Use:

- Python
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0 async
- OpenAPI-generated API documentation

## Data Layer

Use:

- PostgreSQL 16+
- TimescaleDB for time-series data
- Redis for caching, rate limiting, distributed locks, and Celery messaging

## Background Processing

Use:

- Celery
- Celery Beat

Separate queues/workers for:

- collection
- cleaning/pipeline
- analytics
- ML/forecasting

## Infrastructure

Use:

- Docker
- Docker Compose
- Nginx or equivalent reverse proxy

The complete project must be runnable locally with:

```bash
docker compose up
```

---

# 2. MOST IMPORTANT PRODUCT PRINCIPLE

The platform is a **statistical intelligence system**, not a UI demo with fake hardcoded charts.

The application architecture must reflect this data flow:

```text
AIRLINE WEBSITES + OTA PLATFORMS
                ↓
        COLLECTION ENGINE
                ↓
      RAW FARE OBSERVATIONS
                ↓
 CLEANING + NORMALISATION PIPELINE
                ↓
     CLEAN FARE OBSERVATIONS
                ↓
 ┌──────────────┼──────────────┐
 ↓              ↓              ↓
INDEX       LEAD-TIME      DATA QUALITY
ENGINE      ANALYTICS
 ↓              ↓
 └─────── EXPLAIN ────────────┘
                ↓
      ANOMALY / SURGE ENGINE
                ↓
         VALIDATION ENGINE
                ↓
        FORECASTING ENGINE
                ↓
       CPI AUGMENTATION ENGINE
                ↓
       API + DASHBOARD + REPORTS
```

The system must clearly separate:

### Write Path

```text
Collection
→ Raw Storage
→ Cleaning
→ Analytics
→ Derived Statistical Products
```

### Read Path

```text
Precomputed Aggregates
→ FastAPI
→ Next.js Dashboard
```

The API must **never trigger scraping directly**.

---

# 3. CORE DATA PIPELINE

Implement the system around these seven stages.

## Stage 1 — COLLECT

Build a source adapter architecture.

Each source should have an isolated adapter.

Example sources:

### Airlines

- IndiGo
- Air India
- Air India Express
- Akasa Air
- SpiceJet

### OTAs

- MakeMyTrip
- Goibibo
- Yatra
- Cleartrip
- EaseMyTrip
- Ixigo

Use a common adapter interface.

Conceptually:

```python
BaseSourceAdapter
    ↓
IndiGoAdapter
AirIndiaAdapter
AkasaAdapter
SpiceJetAdapter
MakeMyTripAdapter
GoibiboAdapter
...
```

Every adapter must support:

- source code
- source type
- adapter version
- rate limits
- fetch
- parse

The collection layer must enforce:

- robots.txt awareness
- per-source rate limits
- caching
- circuit breaking
- scheduled collection
- audit logging

The application must **not attempt to bypass**:

- CAPTCHAs
- login walls
- access controls
- other anti-bot protections

If a source is unavailable:

```text
SOURCE DOWN
→ FALLBACK SOURCE
→ DATA QUALITY FLAG
→ INDEX CONTINUES
```

The system must degrade gracefully.

---

# 4. STAGE 2 — CLEAN AND NORMALISE

Implement a fixed cleaning pipeline in this exact conceptual order:

```text
1. Schema Validation
        ↓
2. Normalisation
        ↓
3. Deduplication
        ↓
4. Missing Value Handling
        ↓
5. Outlier Detection
        ↓
6. Fare Decomposition
        ↓
7. Quality Scoring
```

Raw observations must be:

- immutable
- append-only
- auditable

Never overwrite raw observations.

Create cleaned/derived observations separately.

Every observation should receive a quality score from:

```text
0–100
```

Quality factors should include:

- completeness
- source reliability
- timestamp validity
- fare consistency
- duplicate status
- route validity
- tax consistency
- availability validity

Quality bands:

```text
85–100 → HIGH CONFIDENCE
60–84  → MEDIUM CONFIDENCE
0–59   → LOW CONFIDENCE
```

By default, only observations with quality >= 60 should enter index calculations.

The threshold and methodology version must be traceable.

---

# 5. DATABASE DESIGN

Implement the data model around the following groups.

## Reference Tables

- airports
- airlines
- routes
- route_weights
- sources
- events
- dgca_benchmarks
- cpi_reference

## Time-Series Tables

### Immutable raw data

```text
fare_observations_raw
```

### Cleaned analytical data

```text
fare_observations
```

Both should be designed appropriately for TimescaleDB/time-series usage.

## Derived Statistical Tables

- index_values
- leadtime_curves
- volatility_metrics
- anomalies
- forecasts
- backtest_runs
- cpi_simulations

## Operational and Quality Tables

- scrape_runs
- data_quality_flags
- api_keys
- audit_log

Everything important must be versioned where appropriate:

- methodology_version
- model_version
- weight_set_version
- adapter_version

Any displayed statistical value should be traceable back to the methodology and source inputs that generated it.

---

# 6. ROW LEVEL SECURITY AND API SECURITY

Security is mandatory.

Implement proper authentication and authorization with roles:

```text
PUBLIC
ANALYST
ADMIN
```

Use scoped permissions/API keys where applicable.

## RLS Requirement

Enable and enforce **Row Level Security (RLS)** on every database table containing protected, operational, user-specific, administrative, or scoped data.

Do not merely add frontend restrictions.

Security must be enforced at the database/data-access level.

Examples include:

- API keys
- audit logs
- collection controls
- scrape runs
- admin operations
- user-specific settings
- protected analytical datasets where access is scoped

Public data can have explicit read policies where intended.

For every API endpoint:

- authenticate where required
- validate authorization/scopes
- ensure the underlying query respects RLS/data-access rules
- never rely solely on frontend role checks

Implement least-privilege access.

Also include:

- per-key rate limiting
- rate limit headers
- encrypted secrets/environment variables
- no secrets committed to source code
- audit logging for sensitive actions
- admin-only collection triggers
- secure API key handling

---

# 7. DASHBOARD — MAIN COMMAND CENTRE

Create `/dashboard`.

This should be the executive overview of India's airfare market.

Display KPI cards such as:

- India Airfare Index
- Month-over-Month change
- Routes Tracked
- Airlines Tracked
- OTA Sources
- Flights Monitored
- Total Data Points

Values must come from real seeded/calculated application data, not random UI placeholders.

## Main Dashboard Sections

### 1. India Airfare Index Trend

Interactive chart supporting:

- daily
- weekly
- monthly
- yearly

### 2. Top Price Increases

Routes with the largest positive movement.

### 3. Top Price Decreases

Routes with falling fares.

### 4. Airfare Pressure Map

India map showing:

- HIGH pressure
- MEDIUM pressure
- LOW pressure

Bundle the required India GeoJSON so the demo works offline.

### 5. Key Insights

Generate insight cards based on actual analytics.

Example style:

> Delhi–Mumbai prices are significantly above their 30-day seasonal baseline.

> Last-minute booking premiums increased this week.

Do not hardcode insight text independently of the underlying data.

---

# 8. AIRFARE PRICE INDEX

Create `/index`.

The index is the statistical heart of the application.

Support:

## National Index

A headline index with a defined base period.

## Regional Indices

- North India
- South India
- East India
- West India

## Route Indices

Examples:

- DEL-BOM
- DEL-BLR
- BOM-BLR
- DEL-CCU
- BLR-HYD
- MAA-DEL

Route weighting should support versioned DGCA passenger-traffic-based weights.

Show:

- current value
- previous value
- percentage movement
- trend chart
- methodology version
- source information

Every major statistical panel must include a visible methodology/source reference.

---

# 9. ROUTE INTELLIGENCE

Create:

```text
/routes
/routes/[routeCode]
```

Each route page should show:

### Key Metrics

- Current Average Fare
- 7-Day Average
- 30-Day Average
- Yearly Average
- Route Index
- Monthly Change
- Yearly Change

### Fare Trend

Interactive historical chart.

### Airline Comparison

Compare available airlines.

### OTA Comparison

Compare:

- Airline Direct
- MakeMyTrip
- Goibibo
- Yatra
- Cleartrip
- EaseMyTrip
- Ixigo

### Fare Composition

Visualise:

```text
Base Fare
+ Taxes
+ UDF
+ Airport Charges
+ Convenience Fee
────────────────────
Final Consumer Fare
```

### Route Insights

Show data-driven insights and anomalies.

---

# 10. LEAD-TIME INTELLIGENCE

Create `/lead-time`.

Support these booking windows:

```text
T+1
T+7
T+15
T+30
T+45
```

Build a lead-time fare curve.

Show:

- average fare by booking window
- last-minute premium
- early booking advantage
- booking pressure
- route-specific elasticity
- seasonal elasticity

Example:

```text
T+45 → ₹5,200
T+30 → ₹5,600
T+15 → ₹6,300
T+7  → ₹7,900
T+1  → ₹11,800
```

All displayed values must come from calculated data.

---

# 11. ANOMALY AND SURGE INTELLIGENCE

Create:

```text
/anomalies
/anomalies/[anomalyId]
```

The anomaly engine should compare:

```text
Expected Fare
vs
Observed Fare
```

Calculate:

- expected fare
- observed fare
- deviation percentage
- severity

Severity levels:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Show factor attribution where supported by the model.

Potential factors:

- weekend demand
- low seat availability
- festival proximity
- short booking window
- seasonal demand
- other calculated factors

The factor breakdown should be interpretable.

Clearly distinguish:

### Market anomaly

Actual unusual airfare movement.

### Data/scraper anomaly

Bad or suspicious collection behavior.

For example, identical fares across thousands of records should trigger a **data-quality alert**, not automatically be classified as a market surge.

---

# 12. EVENT AND SEASONAL INTELLIGENCE

Include an event calendar supporting:

- festivals
- national holidays
- long weekends
- major travel periods
- seasonal peaks

Allow the analytics layer to calculate:

- normal-period fares
- event-period fares
- event premium
- route-specific seasonal behavior

Event proximity should also be available as a feature for:

- anomaly detection
- forecasting

---

# 13. VOLATILITY ENGINE

Create volatility analytics supporting:

- standard deviation
- coefficient of variation
- rolling 7-day volatility
- rolling 30-day volatility
- price range
- abnormal movement frequency

Create a composite:

# Airfare Volatility Score

With:

```text
LOW
MEDIUM
HIGH
```

---

# 14. AIRLINE AND OTA PRICE DIVERGENCE

Compare the same itinerary across sources where matching observations are available.

Matching criteria should conceptually include:

- route
- flight
- departure datetime
- fare class
- observation window

Calculate:

- source-to-source spread
- convenience fee differences
- discount detection
- inconsistency flags

Feed meaningful divergence outliers back into the data-quality framework.

---

# 15. CPI AUGMENTATION SIMULATOR

Create `/cpi-simulator`.

This is a major policy-facing feature.

Display:

- Base CPI
- Airfare Index
- Airfare Weight
- Simulated Augmented Index

Use:

```text
Augmented Index =
Base CPI × (1 − w)
+
Airfare Index × w
```

Default airfare weight:

```text
2.5%
```

Allow users to:

- adjust the airfare weight
- run scenario analysis
- compare multiple scenarios
- view sensitivity charts

Show the data flow visually:

```text
Existing CPI
      ↓
Airfare Signal
      ↓
Scenario Weighting
      ↓
Simulated Augmented Measurement
```

A persistent disclaimer must always be visible:

> This module is a simulation for analytical demonstration. It does not represent an official CPI revision or official NSO methodology.

The disclaimer must:

- not be dismissible
- be visible on the page
- be included in relevant API responses

CPI data must always display:

- data vintage
- base year

Never silently mix CPI vintages.

---

# 16. BACKTESTING LAB

Create `/backtesting`.

Use DGCA benchmark data.

Support:

- minimum 30-day out-of-sample backtest
- ideally support longer periods

Calculate:

- MAE
- RMSE
- MAPE
- Pearson Correlation
- Directional Accuracy

Display:

### Benchmark Overlay

```text
Our Index
vs
DGCA Benchmark
```

### Residual/Error Chart

Show errors separately.

Allow configuration for:

- date range
- route subset
- estimator variant

Clearly display the train/test boundary.

Metrics must always be calculated from stored data.

Never hardcode evaluation metrics.

---

# 17. FORECASTING ENGINE

Create `/forecast`.

Forecast:

- route fares
- national airfare index

Default forecast horizon:

```text
14 days
```

Support baseline models:

- Seasonal Moving Average
- Exponential Smoothing
- Seasonal Baseline

Architecture should allow advanced models:

- SARIMA
- Gradient Boosting
- Time-Series Regression

Every forecast must include:

- prediction
- lower bound
- upper bound
- model version

Never render a point forecast alone.

Show:

### Model Comparison Table

```text
Model
Validation MAPE
Selected?
```

Also display:

# Expected Airfare Pressure

```text
LOW
MEDIUM
HIGH
```

---

# 18. DATA EXPLORER

Create `/data-explorer`.

Allow users to inspect observations.

Columns should include:

- timestamp
- origin
- destination
- airline
- flight
- departure date
- lead days
- fare class
- base fare
- tax
- fees
- total fare
- source
- quality score

Support filters:

- date range
- route
- airline
- OTA
- fare class
- lead time
- source
- quality band

Allow:

### Raw vs Cleaned Toggle

Show what changed during the cleaning pipeline.

Support:

- CSV export
- JSON export

Use:

- server-side pagination
- capped exports
- rate limiting

Never run unbounded database queries.

---

# 19. API PORTAL

Create:

```text
/api-portal
/api-portal/keys
```

Provide an in-app API documentation experience.

Support endpoints conceptually under:

```text
/api/v1
```

Include:

```text
GET /api/v1/index
GET /api/v1/index/route/{route_code}
GET /api/v1/fares
GET /api/v1/anomalies
GET /api/v1/forecast
GET /api/v1/routes
GET /api/v1/airlines
GET /api/v1/lead-time
GET /api/v1/cpi-simulation
GET /api/v1/backtest
GET /api/v1/data-quality
```

Use a consistent response structure:

```json
{
  "data": {},
  "meta": {},
  "methodology_version": "",
  "disclaimer": null
}
```

Support:

- date filters
- route filters
- daily/weekly/monthly granularity
- pagination

Add:

- copyable API examples
- endpoint documentation
- Try It panel where authorization allows
- OpenAPI documentation

---

# 20. COLLECTION ENGINE CONTROL

Create `/collection`.

Display per-source status.

For every source show:

- last run
- records found
- valid records
- failed records
- success rate
- latency
- source status

Include scheduler information:

- next run
- cron schedule
- current status

Manual trigger must be:

```text
ADMIN ONLY
```

Implement audit logging for manual triggers.

---

# 21. SITE NAVIGATION

Implement a polished navigation system.

## Public Marketing Navigation

Include:

- Home
- Platform / Features
- Methodology
- About
- FAQ
- API Portal
- Dashboard CTA

## Application Navigation

Use a professional sidebar.

Include:

- Dashboard
- Airfare Index
- Routes
- Lead-Time Intelligence
- Anomalies
- Forecast
- Backtesting
- CPI Simulator
- Data Explorer
- Collection
- API Portal
- Reports
- Settings

The active page must be clearly visible.

Navigation must be:

- responsive
- keyboard accessible
- mobile friendly

---

# 22. ABOUT PAGE

Create:

```text
/about
```

Explain:

## What is India Airfare Intelligence?

Explain the platform as a high-frequency airfare statistical intelligence system.

## The Problem

Explain dynamic airfare pricing and fragmented online observations.

## The Solution

Explain:

```text
Collect
→ Clean
→ Measure
→ Explain
→ Validate
→ Predict
→ Augment
```

## Who It Is For

- Policymakers
- Statistical organisations
- Regulators
- Economists
- Researchers
- Aviation analysts

## Principles

- Statistical First
- Consumer-Centric
- Explainable
- Reproducible
- Resilient
- Policy-Oriented

Include internal links to:

- Methodology
- Dashboard
- Airfare Index
- API Portal

---

# 23. MARKETING / LANDING PAGE

Create a polished homepage.

The hero section should immediately communicate:

# India's Airfare Market, Measured Intelligently.

Explain that the platform transforms fragmented airfare observations into statistical intelligence.

Include a primary CTA **above the fold / above the main hero field or form area**.

The CTA should be highly visible before the user needs to scroll.

Suggested CTA hierarchy:

### Primary CTA

```text
Explore the Dashboard
```

### Secondary CTA

```text
Understand the Methodology
```

Also include internal links to:

- Dashboard
- Index
- Methodology
- About
- API Portal

---

# 24. INTERNAL LINKING REQUIREMENT

Implement meaningful internal linking across the entire website.

Examples:

### Dashboard

Link to:

- Route Intelligence
- Anomaly Details
- Forecast
- Methodology

### Route Pages

Link to:

- Lead-Time Intelligence
- Related Anomalies
- Forecast
- Data Explorer

### CPI Simulator

Link to:

- Methodology
- Backtesting
- Airfare Index

### About Page

Link to:

- Dashboard
- Methodology
- API Portal

### FAQ

Link relevant answers to detailed pages.

Internal links must be contextually useful for both:

- user navigation
- SEO

Do not create meaningless link spam.

---

# 25. BREADCRUMBS

Add breadcrumbs to all applicable nested pages.

Examples:

```text
Home
→ Routes
→ DEL-BOM
```

```text
Home
→ Anomalies
→ Anomaly Details
```

```text
Home
→ API Portal
→ API Keys
```

Requirements:

- semantic markup
- clickable parent levels
- current page clearly identified
- schema-friendly breadcrumb structure where applicable

---

# 26. CUSTOM 404 PAGE

Create a polished custom:

```text
404 Not Found
```

page.

It should match the visual identity of the platform.

Include:

- clear error message
- explanation that the requested intelligence page could not be found
- button to Dashboard
- button to Home
- helpful links to major sections

Do not use a generic browser-style error page.

---

# 27. FAQ SECTION

Create a dedicated:

```text
/faq
```

page and include an FAQ section where useful on the homepage.

Include at least these 5 substantial FAQs:

### 1. What is the India Airfare Price Index?

Explain how the platform aggregates representative airfare observations into a measurable index.

### 2. How does the platform collect airfare data?

Explain the adapter architecture, scheduled collection, ethical safeguards, and source resilience.

### 3. How are unreliable or bad fare observations handled?

Explain validation, normalisation, deduplication, outlier detection, and quality scoring.

### 4. Is the CPI Augmentation Simulator an official CPI calculation?

Clearly state that it is an analytical simulation and not an official revision of NSO methodology.

### 5. What happens if an airline or OTA data source becomes unavailable?

Explain:

```text
Source Failure
→ Fallback
→ Quality Flag
→ Continued Index Operation
```

Use FAQ schema markup for SEO where appropriate.

---

# 28. SEO OPTIMISATION

SEO must be implemented properly.

## Every Important Page Must Have

- unique title
- unique meta description
- canonical URL
- Open Graph metadata
- Twitter/social metadata where appropriate

Implement metadata for:

- Home
- About
- FAQ
- Methodology
- Dashboard landing/public pages
- Routes
- API Portal

Use semantic HTML:

- header
- nav
- main
- section
- article
- footer

Implement structured data where appropriate:

- Organization schema
- WebSite schema
- BreadcrumbList schema
- FAQPage schema

Generate:

- sitemap.xml
- robots.txt

Ensure:

- descriptive URLs
- clean slugs
- no duplicate metadata
- canonical handling
- crawlable public pages

Protected application pages should not accidentally expose sensitive/private data to search engines.

---

# 29. IMAGE ACCESSIBILITY

Every meaningful image must have descriptive alt text.

Examples:

Bad:

```text
alt="image"
```

Good:

```text
alt="India map showing regional airfare price pressure"
```

Decorative images should use appropriate empty alt text where necessary.

Charts must also have accessible descriptions.

Provide:

- aria-labels
- chart summaries
- keyboard accessibility where practical

---

# 30. SITE ANALYTICS

Implement privacy-conscious site analytics.

Track useful events such as:

- page views
- dashboard exploration
- CTA clicks
- route page visits
- API portal usage
- documentation interactions
- export actions
- simulator interactions

Do not collect unnecessary personal data.

The analytics implementation should respect the platform principle:

> Zero unnecessary personal data collection.

Create a clean analytics abstraction so the provider can be swapped later.

Track meaningful product events rather than only raw page views.

---

# 31. DESIGN SYSTEM

The design should feel like:

- Bloomberg Terminal meets modern government analytics
- financial intelligence platform
- statistical dashboard
- premium and credible
- clean, restrained, data-first

Avoid:

- travel-booking aesthetics
- excessive gradients
- cartoon illustrations
- flashy animations
- unnecessary glassmorphism

Use:

- strong typography
- clear hierarchy
- spacious layouts
- restrained color palette
- excellent chart readability

Create reusable components for:

## Layout

- Sidebar
- TopBar
- DataModeBadge
- PanelShell

## KPI

- KpiCard
- HeroKpiCard
- DeltaChip

## Status

- SeverityBadge
- QualityIndicator

## Charts

- IndexTrendChart
- FareTrendChart
- LeadTimeCurveChart
- ForecastChart
- BenchmarkOverlayChart
- ResidualChart
- PressureMap
- AirlineBoxPlot
- SourceSpreadChart
- FareCompositionBar
- AttributionBars
- SensitivityChart

## Tables

- ObservationTable
- MoversList
- ModelComparisonTable

## Filters

- FilterBar
- FilterChips

## CPI

- DisclaimerBanner
- ScenarioSlider

---

# 32. ACCESSIBILITY

Meet WCAG 2.1 AA standards.

Ensure:

- sufficient contrast
- keyboard navigation
- visible focus states
- screen-reader labels
- accessible forms
- semantic HTML
- chart descriptions
- non-color-only status indicators

The application must work well across:

- desktop
- tablet
- mobile

---

# 33. DEMO RESILIENCE

The entire platform must remain demonstrable when external internet sources are unavailable.

Implement:

# Data Mode

Clearly display:

```text
LIVE DATA
```

or:

```text
DEMO DATA
```

The UI must never pretend demo data is live data.

Provide deterministic seed data covering:

- multiple routes
- airlines
- OTAs
- lead-time windows
- anomalies
- forecasts
- backtesting
- CPI simulation

The complete guided demo path should work with external network access disabled.

Do not make the frontend depend on live scraping to render.

---

# 34. TESTING

Implement:

## Backend

- unit tests
- integration tests
- pipeline tests
- API tests
- golden-file tests for index calculations

## Frontend

- component tests
- accessibility checks
- end-to-end tests

Test:

- index calculations
- quality scoring
- anomaly detection
- forecasting output bounds
- CPI disclaimer persistence
- API authorization
- RLS policies/access boundaries
- admin-only actions

Include an end-to-end test ensuring the demo works with network access disabled.

---

# 35. REQUIRED FOLDER STRUCTURE

Maintain a clean architecture similar to:

```text
backend/
  app/
    api/
    analytics/
    collection/
    pipeline/
    services/
    db/
    models/
    schemas/
    middleware/
    data_mode/
    guards/
  tests/
  seeds/

frontend/
  src/
    app/
    components/
    lib/
    styles/
    types/
  public/
  tests/

infra/
  docker/
  grafana/
  k8s/

scripts/
```

## Critical Architecture Rule

The analytics package must remain pure.

It must not directly depend on:

- database access
- API layer
- scraping adapters

Analytics functions should receive plain data structures/DataFrames and return deterministic outputs.

This makes statistical calculations:

- reproducible
- testable
- auditable

---

# 36. FINAL IMPLEMENTATION REQUIREMENTS

Build the project as a cohesive production-quality application.

Do not simply create disconnected pages.

Ensure the entire application follows the real data flow:

```text
SOURCE DATA
↓
RAW OBSERVATIONS
↓
CLEANED OBSERVATIONS
↓
QUALITY FILTERING
↓
STATISTICAL COMPUTATION
↓
DERIVED ANALYTICS
↓
API
↓
DASHBOARD
↓
USER INSIGHTS
```

Every important UI metric should trace back to actual seeded or calculated data.

Do not hardcode impressive-looking numbers independently into components.

Every page should include:

- loading states
- empty states
- error states
- responsive behavior

The final product should demonstrate:

1. Statistical rigor
2. Strong system architecture
3. Excellent data flow
4. Auditability
5. Explainability
6. Security
7. RLS enforcement
8. Demo resilience
9. Accessibility
10. SEO optimisation
11. Professional UI/UX

The finished application should feel like a serious platform that could be presented to:

- SIH judges
- government statistical organisations
- aviation regulators
- economists
- policy researchers

rather than simply a hackathon dashboard.