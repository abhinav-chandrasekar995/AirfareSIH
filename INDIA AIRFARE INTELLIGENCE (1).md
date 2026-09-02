# INDIA AIRFARE INTELLIGENCE
## Real-Time Airfare Price Index & CPI Augmentation Platform

### SIH Product & Technical Design Report

---

# 1. Executive Summary

India's domestic airfare market is highly dynamic. Prices vary according to route, airline, booking lead time, demand, seat availability, seasonality, festivals, weekends, and other market conditions.

The SIH problem statement asks for an end-to-end software platform capable of collecting airfare observations from airline and Online Travel Aggregator (OTA) sources, cleaning and normalising the data, constructing a representative Airfare Price Index, visualising price trends, and exposing the resulting information through an API. It also calls for multiple advance-purchase windows, route weights based on DGCA passenger-traffic data, and at least 30 days of back-testing against publicly available DGCA fare data.

The proposed product is:

# **INDIA AIRFARE INTELLIGENCE**

A government-oriented statistical intelligence platform that transforms fragmented online airfare observations into:

- a national Airfare Price Index;
- route-level price intelligence;
- lead-time elasticity analysis;
- anomaly and airfare-surge detection;
- forecasting;
- airline/OTA comparison;
- fare-component analysis;
- data-quality monitoring;
- DGCA benchmark validation;
- and a CPI Augmentation Simulator.

The central philosophy is:

> **Collect → Clean → Measure → Explain → Validate → Predict → Augment**

The product should not feel like a flight-booking website.

It should feel like a **financial/statistical intelligence platform for India's air-travel market**.

---

# 2. Problem Statement

The original SIH problem statement identifies a gap between traditional/manual price collection and the increasingly digital airfare market. It asks for automated collection from major airline websites and OTAs, representative city-pair coverage, multiple booking windows, data cleaning, index construction, visualisation, and API access.

The central technical problem can therefore be expressed as:

> **How can millions of dynamic airfare observations be converted into a reliable, representative and explainable statistical measure of airfare inflation in India?**

This creates five major engineering challenges:

1. **Data acquisition**
2. **Data quality and normalisation**
3. **Statistical index construction**
4. **Intelligence and interpretation**
5. **Validation and policy application**

Our product addresses all five in one integrated system.

---

# 3. Important Current Context

There is an important point your team should understand before presenting this to judges.

The SIH problem statement describes the need to move beyond limited/manual airfare collection. However, MoSPI's newer CPI 2024 material states that airfare prices are now being collected from online platforms, alongside other alternative data sources.

The CPI 2024 series was introduced with a new base of 2024=100 and uses HCES 2023-24 expenditure data for weights. It also adopts COICOP 2018 and expands the use of alternative/digital data sources.

Therefore, your product should **not pitch itself as:**

> "MoSPI does not collect online airfare data."

Instead pitch:

> **"We propose a scalable, high-frequency airfare intelligence architecture that continuously collects, normalises, validates and analyses online airfare observations, constructs a transparent route-weighted Airfare Price Index, detects abnormal price movements, validates the index against official benchmarks, and demonstrates how high-frequency airfare information can augment statistical analysis."**

That is a stronger and more defensible proposition.

---

# 4. Product Vision

## Vision

To create India's most transparent, high-frequency software platform for measuring and understanding consumer airfare movements.

## Mission

Convert raw online airfare observations into actionable statistical intelligence for:

- policymakers;
- statistical organisations;
- regulators;
- economists;
- researchers;
- aviation analysts;
- and other authorised data consumers.

## Core Product Question

The system should answer:

> **What is happening to airfare prices in India, where is it happening, why is it happening, and what could happen next?**

---

# 5. Product Architecture

The complete system follows this pipeline:

```text
AIRLINE WEBSITES
       +
OTA PLATFORMS
       │
       ▼
DATA COLLECTION ENGINE
       │
       ▼
RAW FARE DATA
       │
       ▼
DATA CLEANING & NORMALISATION
       │
       ▼
FARE OBSERVATION DATABASE
       │
       ├───────────────┐
       │               │
       ▼               ▼
ROUTE ANALYTICS    LEAD-TIME ANALYTICS
       │               │
       └───────┬───────┘
               ▼
         INDEX ENGINE
               │
               ▼
      INDIA AIRFARE INDEX
               │
      ┌────────┼──────────┐
      │        │          │
      ▼        ▼          ▼
   ANOMALY  FORECAST    CPI
   ENGINE   ENGINE    SIMULATOR
      │        │          │
      └────────┼──────────┘
               ▼
        API + DASHBOARD
               │
               ▼
       REPORTS / INSIGHTS
```

---

# 6. Product Design Principles

The platform should follow six principles.

## 6.1 Statistical First

The index methodology must be more important than visual effects.

## 6.2 Consumer-Centric

Where possible, measure the final fare a traveller actually faces rather than only an advertised base fare.

## 6.3 Explainable

Every significant price movement should have an interpretable reason or contributing factors.

## 6.4 Reproducible

A judge should be able to understand how an index value was generated.

## 6.5 Resilient

The system should continue functioning even when one source becomes unavailable.

## 6.6 Policy-Oriented

The final output should have relevance beyond flight-price comparison.

---

# 7. Core Product Modules

The product consists of 13 major modules.

---

# 7.1 Dashboard

The Dashboard is the executive command centre.

## Main KPI Cards

```text
INDIA AIRFARE INDEX
127.4
↑ 7.4% MoM

ROUTES TRACKED
142

AIRLINES
12

OTA SOURCES
5

FLIGHTS MONITORED
18,742

DATA POINTS
2.4M
```

These numbers are illustrative; the actual dashboard should show live system values.

## Main visualisations

### Airfare Index Trend

Daily/weekly/monthly/yearly index movement.

### Top Price Increases

Routes with the highest positive movement.

### Top Price Decreases

Routes experiencing falling fares.

### Airfare Pressure Map

An India map showing:

- high price pressure;
- medium pressure;
- low pressure.

### Key Insights

Automatically generated statements such as:

> Delhi–Mumbai prices are 18% above their 30-day seasonal baseline.

> Last-minute booking premiums increased sharply this week.

> Multiple routes are experiencing simultaneous price pressure.

---

# 7.2 Airfare Price Index

This is the **statistical heart of the project**.

The platform should construct:

## National Index

A single headline number:

> **India Airfare Price Index = 127.4**

with a defined base period.

## Regional Indices

- North India
- South India
- East India
- West India

## Route Indices

Examples:

- DEL–BOM
- DEL–BLR
- BOM–BLR
- DEL–CCU
- BLR–HYD
- MAA–DEL

The SIH problem specifically identifies representative city-pairs and expects their selection to be informed by DGCA passenger-traffic data.

---

# 7.3 Route Intelligence

Every major route should have its own analytical page.

Example:

## DEL → BOM

```text
Current Average Fare       ₹10,450
7-Day Average              ₹9,620
30-Day Average             ₹8,150
Yearly Average             ₹7,250

Route Index                131.4
Monthly Change             +12.3%
Yearly Change              +44.1%
```

The actual values would be generated by the system.

## Route page components

### Fare trend

Shows price movement over time.

### Airline comparison

```text
IndiGo
Air India
Air India Express
Akasa
SpiceJet
```

### OTA comparison

```text
Airline Direct
MakeMyTrip
Goibibo
Yatra
Cleartrip
EaseMyTrip
Ixigo
```

### Fare composition

```text
Base Fare
+ Taxes
+ UDF
+ Airport Charges
+ Convenience Fee
-------------------
Final Consumer Fare
```

This supports the problem statement's requirement to separate base fare, taxes, user-development fees and convenience charges.

---

# 7.4 Lead-Time Intelligence

This is one of the strongest features because the PS explicitly requires multiple advance-purchase windows:

- T+1
- T+7
- T+15
- T+30
- T+45.

Instead of simply storing these observations, the platform analyses the relationship.

Example:

```text
Booking Window       Average Fare

T+45                    ₹5,200
T+30                    ₹5,600
T+15                    ₹6,300
T+7                     ₹7,900
T+1                    ₹11,800
```

This generates a:

## Lead-Time Fare Curve

The system can calculate:

- last-minute premium;
- early-booking advantage;
- booking pressure;
- route-specific elasticity;
- seasonal elasticity.

---

# 7.5 Anomaly & Surge Intelligence

This is the primary "wow" feature.

The system establishes an expected baseline for a route and compares current prices against it.

Example:

```text
DEL → BOM

Expected Fare       ₹6,200
Observed Fare      ₹10,450

Deviation           +68.5%

Severity             HIGH
```

The system can then analyse contributing factors.

```text
Weekend Demand          +21%
Low Seat Availability   +18%
Festival Proximity      +14%
Short Booking Window    +11%
Other                    +4%
```

These values are illustrative. The real system must calculate them from actual observations and clearly label any model-based attribution.

---

# 7.6 Event & Seasonal Intelligence

Airfare is strongly influenced by temporal patterns.

The platform should maintain an event/holiday calendar containing relevant:

- festivals;
- national holidays;
- long weekends;
- major travel periods;
- seasonal peaks.

The system can compare:

```text
Normal Period
       vs.
Event Period
```

Example:

> Diwali-period airfare is 46% above the seasonal baseline on selected routes.

This can feed directly into anomaly detection.

---

# 7.7 Airfare Volatility Engine

Price level alone is insufficient.

Two routes may have the same average fare but dramatically different volatility.

The platform should calculate:

- standard deviation;
- coefficient of variation;
- rolling volatility;
- price range;
- abnormal movement frequency.

Example:

| Route | Average Fare | Volatility |
|---|---:|---|
| DEL–BOM | ₹6,100 | Low |
| BLR–DEL | ₹7,200 | Medium |
| BOM–GOI | ₹9,100 | High |

This creates an:

# Airfare Volatility Score

---

# 7.8 Airline & OTA Price Divergence

A very useful analytical layer is comparing the same itinerary across sources.

Example:

```text
Airline Direct       ₹6,200
MakeMyTrip           ₹6,350
Goibibo              ₹6,180
Yatra                ₹6,420
Cleartrip            ₹6,300
```

The system can identify:

- source-to-source differences;
- convenience fees;
- discounts;
- price spreads;
- data inconsistencies.

This also provides a strong data-quality validation mechanism.

---

# 7.9 CPI Augmentation Simulator

This should be the **policy-facing hero feature**.

MoSPI's CPI 2024 series has already expanded the use of alternative data sources, including online-platform collection for airfare.

Your product should therefore position this module as a **simulation and analytical augmentation layer**, not as a replacement for official CPI.

## Interface

```text
BASE CPI
142.1

AIRFARE INDEX
158.7

AIRFARE WEIGHT
2.5%

SIMULATED AUGMENTED INDEX
143.0
```

Then:

```text
Existing CPI
       ↓
Airfare signal
       ↓
Scenario weighting
       ↓
Simulated augmented measurement
```

The system should clearly state:

> "This module is a simulation for analytical demonstration. It does not represent an official CPI revision or official NSO methodology."

---

# 7.10 Backtesting Lab

The PS requires at least 30 days of back-tested results against publicly available DGCA monthly average-fare data.

This should become a visible product module.

## Comparison

```text
OUR AIRFARE INDEX
       vs.
DGCA BENCHMARK
```

## Metrics

- MAE
- RMSE
- MAPE
- correlation
- trend accuracy

Example display:

```text
Correlation       0.91
MAPE              3.4%
MAE               ₹240
Trend Accuracy    94%
```

These are example UI values only.

---

# 7.11 Forecasting Engine

Once sufficient historical observations exist, the platform can estimate future airfare pressure.

Possible forecasting approaches:

### MVP

- moving averages;
- exponential smoothing;
- seasonal baselines.

### Advanced

- SARIMA;
- Prophet-style models;
- gradient boosting;
- time-series regression.

### Output

```text
NEXT 14 DAYS

Expected Airfare Pressure
       HIGH

Forecast
₹7,900 – ₹9,200
```

The system should display confidence intervals rather than presenting a single forecast as certain.

---

# 7.12 Data Explorer

This module is primarily for transparency.

Users can inspect individual observations.

Example:

```text
Timestamp
Origin
Destination
Airline
Flight
Departure Date
Lead Days
Fare Class
Base Fare
Tax
Fee
Total Fare
Source
Quality Score
```

Filters:

- date;
- route;
- airline;
- OTA;
- fare class;
- lead time;
- source;
- quality.

This makes the platform auditable.

---

# 7.13 API Portal

The SIH problem specifically expects an API that NSO/RBI can consume.

Example endpoints:

```text
GET /api/v1/index

GET /api/v1/index/route/DEL-BOM

GET /api/v1/fares

GET /api/v1/anomalies

GET /api/v1/forecast

GET /api/v1/routes

GET /api/v1/airlines

GET /api/v1/cpi-simulation
```

The API should support:

- JSON;
- date filtering;
- route filtering;
- aggregation;
- authentication;
- rate limiting;
- API documentation.

---

# 8. Data Architecture

The core database can use PostgreSQL.

## Main tables

### airports

```text
airport_id
iata_code
city
state
region
latitude
longitude
```

### routes

```text
route_id
origin
destination
distance
region
route_weight
active
```

### airlines

```text
airline_id
name
code
```

### sources

```text
source_id
source_name
source_type
url
status
```

### fare_observations

```text
observation_id
timestamp
source
origin
destination
airline
flight_number
departure_datetime
lead_days
fare_class
base_fare
taxes
udf
convenience_fee
total_fare
availability
currency
quality_score
```

### index_values

```text
index_id
date
level
route
index_value
weight
```

### anomalies

```text
anomaly_id
route
timestamp
expected_fare
observed_fare
deviation
severity
reason
```

### forecasts

```text
forecast_id
route
forecast_date
prediction
lower_bound
upper_bound
model_version
```

### scrape_runs

```text
run_id
source
started_at
completed_at
records_found
records_valid
records_failed
status
```

---

# 9. Data Collection Architecture

The scraper should not be one monolithic script.

Use a source-adapter architecture.

```text
Scraping Orchestrator
        │
        ├── IndiGo Adapter
        ├── Air India Adapter
        ├── Akasa Adapter
        ├── SpiceJet Adapter
        ├── OTA Adapter
        └── etc.
```

This means if one website changes its frontend, the entire system does not have to be rewritten.

Technology options:

- Python;
- Playwright;
- Scrapy;
- Requests where appropriate.

The SIH problem explicitly calls for handling JavaScript-rendered pages, session management, CAPTCHAs/anti-bot conditions and ethical scraping safeguards.

The implementation must comply with applicable website terms, robots directives and rate limits. The system should not attempt to bypass access controls.

---

# 10. Data Pipeline

The pipeline should be:

```text
RAW OBSERVATION
       ↓
SCHEMA VALIDATION
       ↓
NORMALISATION
       ↓
DEDUPLICATION
       ↓
MISSING-VALUE HANDLING
       ↓
OUTLIER DETECTION
       ↓
FARE DECOMPOSITION
       ↓
QUALITY SCORING
       ↓
VALID OBSERVATION
```

---

# 11. Data Quality Framework

Every observation should have a quality score.

Possible factors:

```text
Completeness
Source Reliability
Timestamp Validity
Fare Consistency
Duplicate Status
Route Validity
Tax Consistency
Availability Validity
```

Output:

```text
Quality Score: 94/100
Status: HIGH CONFIDENCE
```

This is especially valuable for a statistical product.

---

# 12. Index Construction

The index should be transparent.

## Step 1 — Define basket

Select representative routes.

Example:

```text
DEL-BOM
DEL-BLR
BOM-BLR
DEL-CCU
BLR-HYD
MAA-DEL
...
```

The PS specifically asks for a representative city-pair basket based on DGCA passenger-traffic data.

## Step 2 — Assign route weights

Example:

```text
DEL-BOM       18%
DEL-BLR       15%
BOM-BLR       12%
DEL-CCU        9%
BLR-HYD        8%
...
```

These are example weights only.

## Step 3 — Calculate route-level price measure

Use robust statistics such as:

- median;
- trimmed mean;
- weighted mean.

Median/robust aggregation can reduce the influence of extreme observations.

## Step 4 — Convert to index

Conceptually:

```text
Route Index =
Current Route Price
-------------------
Base Route Price
× 100
```

## Step 5 — Aggregate routes

Conceptually:

```text
National Index =
Σ(Route Index × Route Weight)
```

The exact methodology should be documented and validated rather than chosen purely for convenience.

---

# 13. Why Robust Statistics Matter

Airfare data will contain:

- sold-out flights;
- unusual promotions;
- premium fares;
- scraping errors;
- duplicated observations;
- sudden genuine price spikes.

Therefore, blindly taking an arithmetic mean can produce misleading results.

The platform should compare:

- mean;
- median;
- trimmed mean;
- weighted median.

Then choose the methodology based on empirical robustness.

---

# 14. ML/AI Layer

AI should support the statistical system, not replace it.

## Recommended AI/ML features

### 1. Anomaly detection

Methods:

- Z-score;
- IQR;
- MAD;
- Isolation Forest.

### 2. Forecasting

Predict:

- route fares;
- index movement;
- price pressure.

### 3. Missing observation estimation

Use carefully controlled imputation where statistically justified.

### 4. Event impact detection

Detect unusual changes associated with known calendar events.

### 5. Scraper anomaly detection

Detect:

> "The source suddenly returned the exact same fare for 2,000 observations."

That may indicate a scraper failure rather than a real market phenomenon.

---

# 15. Dashboard Information Architecture

The primary navigation should be:

```text
🏠 Dashboard

📊 Airfare Index

✈ Route Intelligence

🚨 Anomaly Intelligence

📈 Lead-Time Insights

🧮 CPI Simulator

🔮 Backtesting & Forecasting

🗄 Data Explorer

🔌 API Portal

📑 Reports

⚙ Settings
```

---

# 16. Visual Design

The UI should look like a combination of:

- Bloomberg;
- RBI/financial dashboards;
- modern SaaS analytics;
- government statistical portals.

Avoid making it look like:

- MakeMyTrip;
- a consumer flight-booking website;
- a generic AI dashboard.

## Recommended style

### Colours

Primary:

- deep navy;
- white;
- cool grey.

Accent:

- blue/purple for analytics;
- green for positive movement;
- red for abnormal price pressure;
- amber for warnings.

### Components

Use:

- cards;
- dense analytical charts;
- map visualisations;
- tables;
- filters;
- drill-down panels;
- status indicators.

---

# 17. User Journey

The ideal judge journey is:

```text
OPEN DASHBOARD
      ↓
SEE INDIA AIRFARE INDEX
      ↓
CLICK "PRICE SURGE"
      ↓
OPEN DEL → BOM
      ↓
SEE LEAD-TIME CURVE
      ↓
SEE AIRLINE/OTA DIFFERENCE
      ↓
SEE ANOMALY EXPLANATION
      ↓
VIEW FORECAST
      ↓
OPEN CPI SIMULATOR
      ↓
COMPARE WITH DGCA
```

The entire demo therefore tells one story.

---

# 18. The Five Hero Features

The product contains many modules, but your SIH presentation should emphasise five.

## 🥇 1. India Airfare Price Index

**Question answered:**

> What is happening to airfare prices?

---

## 🥈 2. Anomaly & Surge Intelligence

**Question answered:**

> Where are prices behaving abnormally?

---

## 🥉 3. Lead-Time & Demand Intelligence

**Question answered:**

> How does booking timing affect prices?

---

## 🏅 4. CPI Augmentation Simulator

**Question answered:**

> How can high-frequency airfare information support statistical analysis?

---

## 🏅 5. Backtesting & Forecasting

**Question answered:**

> Does the system work, and what might happen next?

---

# 19. How the Five Features Reinforce Each Other

This is the most important product relationship.

```text
RAW AIRFARES
     ↓
AIRFARE INDEX
     ↓
LEAD-TIME MODEL
     ↓
EXPECTED PRICE BASELINE
     ↓
ANOMALY DETECTION
     ↓
FORECAST
     ↓
CPI SIMULATION
```

For example:

A fare observation of ₹8,000 contributes to the route-level price distribution.

The route distribution contributes to the Airfare Index.

The same observation contributes to the T+15 lead-time curve.

The lead-time model helps determine whether ₹8,000 is normal or abnormal.

The anomaly system can then flag a price surge.

Historical observations feed the forecasting model.

The resulting index can feed the CPI simulation.

Therefore:

> **One data point powers multiple analytical layers.**

This is what makes the architecture coherent.

---

# 20. Backtesting Strategy

The minimum requirement is 30 days.

The better implementation is:

```text
Historical Data
      ↓
Training Window
      ↓
Index Construction
      ↓
Out-of-Sample Testing
      ↓
DGCA Benchmark
      ↓
Error Analysis
```

Do not simply compare two arbitrary graphs.

Measure:

### MAPE

Mean Absolute Percentage Error.

### MAE

Mean Absolute Error.

### RMSE

Root Mean Square Error.

### Correlation

How closely the two series move together.

### Directional Accuracy

How often the system correctly identifies whether prices increased or decreased.

---

# 21. Forecasting Strategy

The MVP should avoid overly complicated deep learning.

Start with:

### Baseline

Seasonal moving average.

Then:

### Model

SARIMA / gradient boosting / another validated time-series method.

Then compare models.

Example:

```text
Model A
MAPE = 8.2%

Model B
MAPE = 5.9%

Model C
MAPE = 4.7%
```

Select based on validation rather than claiming an AI model is automatically superior.

---

# 22. Security & Reliability

The production architecture should include:

- API authentication;
- role-based access;
- rate limiting;
- encrypted credentials;
- secret management;
- database backups;
- logging;
- monitoring;
- audit trails.

---

# 23. Ethical Scraping

This should be a visible part of the architecture.

The system should implement:

- robots.txt awareness;
- source-specific rate limits;
- caching;
- scheduled collection;
- minimal request frequency;
- no unnecessary load;
- respect for terms of service;
- source attribution.

Do not design the product around bypassing CAPTCHAs or access restrictions.

If a source becomes unavailable:

```text
SOURCE DOWN
     ↓
Fallback Source
     ↓
Data Quality Flag
     ↓
Continue Index
```

---

# 24. Offline/Demo Resilience

This is extremely important for SIH.

Your live demo should **not depend entirely on live scraping**.

Use:

```text
LIVE SCRAPER
     +
CACHED DATA
     +
HISTORICAL DATA
```

If an airline website blocks requests during judging:

```text
Live source unavailable
        ↓
Cached observations
        ↓
Dashboard continues
```

But clearly label simulated/replayed data where applicable.

This prevents one network problem from destroying the presentation.

---

# 25. Development Roadmap

## Phase 1 — Foundation

Build:

- database;
- basic scraper;
- route model;
- fare schema;
- cleaning pipeline.

Target:

```text
5 airlines
3 OTAs
10–15 routes
5 lead-time windows
```

---

## Phase 2 — Index

Build:

- route weights;
- route index;
- national index;
- trend dashboard.

At this point you have a working core product.

---

## Phase 3 — Intelligence

Add:

- lead-time analysis;
- anomaly detection;
- volatility;
- airline/OTA comparison.

---

## Phase 4 — Validation

Add:

- DGCA benchmark;
- 30-day backtest;
- accuracy metrics.

---

## Phase 5 — Advanced Intelligence

Add:

- forecasting;
- event analysis;
- CPI simulation.

---

## Phase 6 — Productionisation

Add:

- API;
- Docker;
- authentication;
- monitoring;
- automated testing;
- documentation.

---

# 26. Suggested Technology Stack

## Frontend

React / Next.js

## Visualisation

Plotly / Apache ECharts

## Backend

Python + FastAPI

## Scraping

Python + Playwright + Scrapy

## Data Processing

Pandas + NumPy + SciPy

## ML

scikit-learn + statsmodels

## Database

PostgreSQL

## Cache

Redis

## Scheduling

Celery / APScheduler

## Deployment

Docker

## API

REST + JSON

---

# 27. Suggested Deployment Architecture

```text
                     INTERNET
                         │
                         ▼
                 ┌──────────────┐
                 │ LOAD BALANCER│
                 └──────┬───────┘
                        │
             ┌──────────┴─────────┐
             ▼                    ▼
        FRONTEND               FASTAPI
                                  │
                     ┌────────────┼────────────┐
                     ▼            ▼            ▼
                 PostgreSQL     Redis       Workers
                                               │
                                               ▼
                                          Scrapers
                                               │
                                  ┌────────────┼────────────┐
                                  ▼            ▼            ▼
                              Airlines       OTAs       External Data
```

---

# 28. Data Flow Example

Consider:

```text
DEL → BOM
IndiGo
Departure: 15 September
Observed: 30 August
Lead Time: 16 days
Total Fare: ₹6,800
```

The observation enters the database.

Then:

```text
Cleaning
   ↓
Quality Score
   ↓
Route Dataset
   ↓
DEL-BOM Index
   ↓
India Index
```

It simultaneously feeds:

```text
Lead-Time Curve
      +
Airline Comparison
      +
OTA Comparison
      +
Anomaly Model
      +
Forecast Model
```

This is why the architecture scales conceptually.

---

# 29. CPI Integration Strategy

The uploaded CPI Excel dataset should be treated as **CPI reference/analysis data**, not as the primary airfare dataset.

Your primary dataset is:

> **the airfare observation database generated by your collection pipeline.**

The CPI data can support:

- historical context;
- inflation comparison;
- classification mapping;
- CPI visualisation;
- simulation.

MoSPI's current CPI framework uses 2024 as the base/reference period and HCES 2023-24 for weights.

Therefore, if your team uses the older CPI dataset for development, clearly identify the vintage/base year rather than mixing it silently with the current 2024-base series.

---

# 30. Product Differentiation

A basic solution might look like:

```text
Scrape
  ↓
Database
  ↓
Average Price
  ↓
Graph
```

Our proposed system is:

```text
Scrape
   ↓
Normalise
   ↓
Validate
   ↓
Weight
   ↓
Airfare Index
   ↓
Lead-Time Intelligence
   ↓
Anomaly Detection
   ↓
Forecasting
   ↓
DGCA Validation
   ↓
CPI Simulation
   ↓
Policy Intelligence
```

That is a substantially stronger product story.

---

# 31. What Makes It SIH-Worthy

The strongest aspects are:

### Government relevance

It addresses official statistical measurement.

### Real-world data engineering

Airline and OTA data is messy and dynamic.

### Statistical methodology

The product isn't just scraping; it constructs an index.

### AI/ML

Used for anomaly detection and forecasting.

### Visualisation

Maps, trends, route analytics and pressure indicators.

### Validation

DGCA benchmark comparison.

### API

Designed for machine consumption.

### Scalability

Architecture can expand from 10 routes to hundreds.

### Explainability

The platform attempts to explain price movements rather than merely display them.

---

# 32. The Winning Demo

The live demo should take approximately this path:

## Step 1

Show:

> **INDIA AIRFARE INDEX — 127.4**

Then:

> "This is our high-frequency measurement of India's airfare market."

---

## Step 2

Click:

> **Top Surge**

Show:

> DEL → BOM +68.5% above expected baseline.

---

## Step 3

Click the route.

Show:

```text
T+45    ₹5,200
T+30    ₹5,600
T+15    ₹6,300
T+7     ₹7,900
T+1    ₹11,800
```

Explain:

> "This is the booking-pressure curve."

---

## Step 4

Show airline/OTA comparison.

Then:

> "We don't just observe the price. We decompose what the consumer actually pays."

---

## Step 5

Open anomaly intelligence.

Show:

> High-price anomaly detected.

Then show contributing factors.

---

## Step 6

Open forecasting.

Show:

> Expected airfare pressure over the next 14 days.

---

## Step 7

Open backtesting.

Show:

> Our index vs DGCA benchmark.

Then display actual calculated metrics.

---

## Step 8 — Final WOW

Open:

# CPI Augmentation Simulator

Show:

```text
Existing CPI
      ↓
Airfare Signal
      ↓
Simulated Augmentation
```

Then say:

> **"We are not building another flight-price tracker. We are converting India's dynamic airfare market into a high-frequency statistical signal that can be analysed, validated and potentially used to augment official economic intelligence."**

That should be your closing statement.

---

# 33. Final Product Tree

```text
INDIA AIRFARE INTELLIGENCE
│
├── Dashboard
│
├── Airfare Price Index
│   ├── India Index
│   ├── Regional Index
│   ├── Route Index
│   ├── Airline Index
│   └── Methodology
│
├── Route Intelligence
│   ├── Route Trends
│   ├── Airline Comparison
│   ├── OTA Comparison
│   ├── Fare Composition
│   └── Route Risk
│
├── Anomaly Intelligence
│   ├── Surge Detection
│   ├── Expected vs Actual
│   ├── Cause Analysis
│   └── Anomaly History
│
├── Lead-Time Intelligence
│   ├── T+1
│   ├── T+7
│   ├── T+15
│   ├── T+30
│   ├── T+45
│   └── Elasticity
│
├── CPI Simulator
│   ├── Existing CPI
│   ├── Airfare Index
│   ├── Weight Simulation
│   ├── Scenario Analysis
│   └── Impact Analysis
│
├── Backtesting & Forecasting
│   ├── DGCA Benchmark
│   ├── 30-Day Backtest
│   ├── Accuracy Metrics
│   └── Forecast
│
├── Data Explorer
│   ├── Raw Data
│   ├── Clean Data
│   ├── Data Quality
│   └── Export
│
├── Collection Engine
│   ├── Airlines
│   ├── OTAs
│   ├── Scheduler
│   └── Monitoring
│
├── API Portal
│
├── Reports
│
└── Settings
```

---

# 34. Final Architecture Philosophy

The entire product can be reduced to one chain:

```text
                REAL-WORLD AIRFARES
                         │
                         ▼
                      COLLECT
                         │
                         ▼
                       CLEAN
                         │
                         ▼
                      MEASURE
                         │
                  AIRFARE INDEX
                         │
                         ▼
                      EXPLAIN
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
        LEAD-TIME                ANOMALIES
        ANALYSIS                  & SURGES
             │                       │
             └───────────┬───────────┘
                         ▼
                       PREDICT
                         │
                     FORECAST
                         │
                         ▼
                      VALIDATE
                         │
                    DGCA BACKTEST
                         │
                         ▼
                       AUGMENT
                         │
                   CPI SIMULATOR
                         │
                         ▼
                  POLICY INTELLIGENCE
```

## The final positioning

**India Airfare Intelligence is not a flight booking platform.**

It is not merely a web scraper.

It is not merely an analytics dashboard.

It is an **end-to-end statistical intelligence platform** that transforms high-frequency online airfare observations into a transparent Airfare Price Index, explains abnormal market movements, analyses booking-window effects, validates itself against external benchmarks, forecasts future price pressure, and demonstrates potential applications to CPI-related analysis.

That distinction should be at the centre of your SIH presentation.