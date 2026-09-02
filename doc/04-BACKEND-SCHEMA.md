# Backend Schema Document
## INDIA AIRFARE INTELLIGENCE

| Field | Value |
|---|---|
| Document | Database Schema & API Contract |
| Version | 1.0 |
| Database | PostgreSQL 16 + TimescaleDB extension |
| ORM / migrations | SQLAlchemy 2.0 (async) + Alembic |
| Last updated | 2026-09-01 |
| Related docs | [PRD](01-PRD.md) · [Architecture](02-ARCHITECTURE.md) · [Design](03-DESIGN.md) · [Folder Structure](05-FOLDER-STRUCTURE.md) |

---

## 1. Schema design principles

1. **Raw is immutable.** `fare_observations_raw` is append-only; nothing updates or deletes it (except retention-policy expiry of the JSONB payload after N days, columns stay).
2. **Everything derived is versioned.** `methodology_version`, `model_version`, `weight_set_version`, `adapter_version` appear wherever a number was computed, so any value is traceable to the code+config that produced it.
3. **Time-series tables are TimescaleDB hypertables**, partitioned on their primary timestamp, with continuous aggregates for the hot rollups the dashboard reads.
4. **No PII.** There is no `users` table with traveller data — this system observes a market, not people. `api_keys` belong to organisations/consumers, not travellers.
5. **Soft-delete is not used** on analytical tables; correction is by superseding row (new `methodology_version`) not mutation, to preserve reproducibility.

---

## 2. Entity relationship overview

```
 airports ---------+
                    |
 airlines --+       |
             |       |
             v       v
          routes <-------- route_weights (versioned)
             ^
             |
        fare_observations_raw --(pipeline)--> fare_observations
             ^                                       |
             |                                       +--> index_values -----> cpi_simulations
        scrape_runs <---- sources                     |                          ^
                                                       +--> leadtime_curves       |
                                                       |                    cpi_reference
                                                       +--> anomalies
                                                       |
                                                       +--> volatility_metrics
                                                       |
                                                       +--> forecasts

        dgca_benchmarks --------------------------> backtest_runs

        events (calendar) --------> feeds anomalies + forecasts (feature input)

        api_keys ---> audit_log
        data_quality_flags <---- pipeline + collection
```

---

## 3. Reference / master tables

### 3.1 `airports`

```sql
CREATE TABLE airports (
    airport_id      SERIAL PRIMARY KEY,
    iata_code       CHAR(3) NOT NULL UNIQUE,
    name            VARCHAR(150) NOT NULL,
    city            VARCHAR(100) NOT NULL,
    state           VARCHAR(100) NOT NULL,
    region          VARCHAR(20)  NOT NULL CHECK (region IN ('NORTH','SOUTH','EAST','WEST','NORTHEAST','CENTRAL')),
    latitude        NUMERIC(9,6) NOT NULL,
    longitude       NUMERIC(9,6) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_airports_region ON airports(region);
```

### 3.2 `airlines`

```sql
CREATE TABLE airlines (
    airline_id      SERIAL PRIMARY KEY,
    iata_code       VARCHAR(3) NOT NULL UNIQUE,     -- '6E', 'AI', 'QP', 'SG', 'IX'
    name            VARCHAR(100) NOT NULL,
    airline_type    VARCHAR(20) NOT NULL DEFAULT 'FSC' CHECK (airline_type IN ('FSC','LCC')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 3.3 `routes`

```sql
CREATE TABLE routes (
    route_id        SERIAL PRIMARY KEY,
    route_code      VARCHAR(9) NOT NULL UNIQUE,        -- 'DEL-BOM'
    origin_id       INTEGER NOT NULL REFERENCES airports(airport_id),
    destination_id  INTEGER NOT NULL REFERENCES airports(airport_id),
    distance_km     NUMERIC(7,1),
    region          VARCHAR(20) NOT NULL,               -- aggregation region for this route
    in_basket       BOOLEAN NOT NULL DEFAULT FALSE,      -- part of the active index basket
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_route_distinct CHECK (origin_id <> destination_id),
    CONSTRAINT uq_route_pair UNIQUE (origin_id, destination_id)
);
CREATE INDEX idx_routes_basket ON routes(in_basket) WHERE in_basket = TRUE;
```

### 3.4 `route_weights` (versioned)

```sql
CREATE TABLE route_weights (
    weight_id           SERIAL PRIMARY KEY,
    weight_set_version  VARCHAR(20) NOT NULL,           -- 'dgca-traffic-2025q2'
    route_id            INTEGER NOT NULL REFERENCES routes(route_id),
    weight              NUMERIC(6,4) NOT NULL CHECK (weight > 0 AND weight <= 1),
    source_description  VARCHAR(200) NOT NULL,           -- 'DGCA domestic passenger traffic, FY2024-25'
    effective_from      DATE NOT NULL,
    effective_to        DATE,                            -- NULL = current
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_weight_version_route UNIQUE (weight_set_version, route_id)
);
CREATE INDEX idx_route_weights_active
    ON route_weights(weight_set_version) WHERE effective_to IS NULL;
```

### 3.5 `sources`

```sql
CREATE TABLE sources (
    source_id       SERIAL PRIMARY KEY,
    source_code     VARCHAR(30) NOT NULL UNIQUE,        -- 'indigo', 'makemytrip'
    source_name     VARCHAR(100) NOT NULL,
    source_type     VARCHAR(20) NOT NULL CHECK (source_type IN ('AIRLINE_DIRECT','OTA')),
    base_url        VARCHAR(300) NOT NULL,
    adapter_version VARCHAR(20) NOT NULL,
    robots_txt_checked_at TIMESTAMPTZ,
    rate_limit_rpm  INTEGER NOT NULL DEFAULT 20,
    status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
                        CHECK (status IN ('ACTIVE','DEGRADED','UNAVAILABLE','DISABLED')),
    reliability_score NUMERIC(5,2) NOT NULL DEFAULT 100.0,  -- rolling, feeds quality scoring
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 3.6 `events` (calendar)

```sql
CREATE TABLE events (
    event_id        SERIAL PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,               -- 'Diwali', 'Republic Day long weekend'
    event_type      VARCHAR(30) NOT NULL
                        CHECK (event_type IN ('FESTIVAL','NATIONAL_HOLIDAY','LONG_WEEKEND','TRAVEL_PEAK','SEASONAL')),
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    affected_regions VARCHAR(20)[],                       -- NULL = national
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_event_dates CHECK (end_date >= start_date)
);
CREATE INDEX idx_events_daterange ON events USING gist (daterange(start_date, end_date, '[]'));
```

### 3.7 `dgca_benchmarks` (external validation data)

```sql
CREATE TABLE dgca_benchmarks (
    benchmark_id    SERIAL PRIMARY KEY,
    route_id        INTEGER REFERENCES routes(route_id),  -- NULL = national-level figure
    period_month    DATE NOT NULL,                         -- first-of-month key
    avg_fare        NUMERIC(10,2) NOT NULL,
    publication_ref VARCHAR(200) NOT NULL,                 -- DGCA source document / URL
    vintage         VARCHAR(20) NOT NULL,                  -- publication vintage label
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_dgca_route_month UNIQUE (route_id, period_month, vintage)
);
```

### 3.8 `cpi_reference` (MoSPI CPI series, explicitly vintaged)

```sql
CREATE TABLE cpi_reference (
    cpi_id          SERIAL PRIMARY KEY,
    series_vintage  VARCHAR(20) NOT NULL,      -- 'cpi-2012-base' | 'cpi-2024-base'
    base_year       VARCHAR(9)  NOT NULL,      -- '2012=100' | '2024=100'
    weight_source   VARCHAR(100) NOT NULL,     -- 'HCES 2023-24' etc.
    coicop_version  VARCHAR(20),               -- 'COICOP 2018'
    period_month    DATE NOT NULL,
    cpi_general     NUMERIC(8,2),
    cpi_transport_communication NUMERIC(8,2),
    airfare_sub_index NUMERIC(8,2),
    airfare_weight_pct NUMERIC(5,3),
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_cpi_vintage_month UNIQUE (series_vintage, period_month)
);
```

---

## 4. Time-series (hot path) tables

### 4.1 `fare_observations_raw` — Tier 0, immutable, hypertable

```sql
CREATE TABLE fare_observations_raw (
    raw_id            BIGSERIAL,
    observed_at       TIMESTAMPTZ NOT NULL,
    source_id         INTEGER NOT NULL REFERENCES sources(source_id),
    scrape_run_id     BIGINT NOT NULL,
    route_code        VARCHAR(9) NOT NULL,
    payload           JSONB NOT NULL,           -- untouched adapter output
    adapter_version   VARCHAR(20) NOT NULL,
    ingested_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (raw_id, observed_at)
);
SELECT create_hypertable('fare_observations_raw', 'observed_at', chunk_time_interval => INTERVAL '1 day');
CREATE INDEX idx_raw_source_time ON fare_observations_raw(source_id, observed_at DESC);
CREATE INDEX idx_raw_route_time  ON fare_observations_raw(route_code, observed_at DESC);
-- Retention: compress chunks older than 30 days; drop raw payload body after 180 days (columns retained via a nulled payload).
SELECT add_compression_policy('fare_observations_raw', INTERVAL '30 days');
```

### 4.2 `fare_observations` — Tier 1, cleaned, hypertable (the analytical core)

```sql
CREATE TABLE fare_observations (
    observation_id    BIGSERIAL,
    raw_id            BIGINT NOT NULL,
    observed_at       TIMESTAMPTZ NOT NULL,
    source_id         INTEGER NOT NULL REFERENCES sources(source_id),
    route_id          INTEGER NOT NULL REFERENCES routes(route_id),
    airline_id        INTEGER NOT NULL REFERENCES airlines(airline_id),
    flight_number     VARCHAR(10) NOT NULL,
    departure_datetime TIMESTAMPTZ NOT NULL,
    lead_days         INTEGER NOT NULL CHECK (lead_days >= 0),
    lead_bucket       VARCHAR(4)  NOT NULL CHECK (lead_bucket IN ('T1','T7','T15','T30','T45')),
    fare_class        VARCHAR(20) NOT NULL DEFAULT 'ECONOMY'
                          CHECK (fare_class IN ('ECONOMY','PREMIUM_ECONOMY','BUSINESS')),

    base_fare         NUMERIC(10,2) NOT NULL CHECK (base_fare >= 0),
    taxes             NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (taxes >= 0),
    udf               NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (udf >= 0),
    airport_charges   NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (airport_charges >= 0),
    convenience_fee   NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (convenience_fee >= 0),
    total_fare        NUMERIC(10,2) NOT NULL CHECK (total_fare > 0),
    currency          CHAR(3) NOT NULL DEFAULT 'INR',

    seats_available   INTEGER,
    availability_status VARCHAR(20) DEFAULT 'AVAILABLE'
                          CHECK (availability_status IN ('AVAILABLE','LIMITED','SOLD_OUT','UNKNOWN')),

    is_outlier        BOOLEAN NOT NULL DEFAULT FALSE,
    imputed_fields    TEXT[] NOT NULL DEFAULT '{}',
    quality_score     NUMERIC(5,2) NOT NULL CHECK (quality_score BETWEEN 0 AND 100),
    quality_band      VARCHAR(10) NOT NULL
                          CHECK (quality_band IN ('HIGH','MEDIUM','LOW')),

    pipeline_version  VARCHAR(20) NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (observation_id, observed_at)
);
SELECT create_hypertable('fare_observations', 'observed_at', chunk_time_interval => INTERVAL '1 day');

CREATE UNIQUE INDEX uq_observation_natural_key ON fare_observations (
    source_id, route_id, flight_number, departure_datetime, fare_class, observed_at
);
CREATE INDEX idx_obs_route_time      ON fare_observations(route_id, observed_at DESC);
CREATE INDEX idx_obs_route_lead_time ON fare_observations(route_id, lead_bucket, observed_at DESC);
CREATE INDEX idx_obs_airline_time    ON fare_observations(airline_id, observed_at DESC);
CREATE INDEX idx_obs_quality         ON fare_observations(quality_band, observed_at DESC);
CREATE INDEX idx_obs_departure       ON fare_observations(departure_datetime);

SELECT add_compression_policy('fare_observations', INTERVAL '30 days');
```

**Continuous aggregates** (the dashboard reads these, never the raw hypertable, for anything beyond a single-route drill-down):

```sql
CREATE MATERIALIZED VIEW route_day_agg
WITH (timescaledb.continuous) AS
SELECT
    route_id,
    time_bucket('1 day', observed_at) AS day,
    AVG(total_fare)                                   AS mean_fare,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY total_fare) AS median_fare,
    percentile_cont(0.25) WITHIN GROUP (ORDER BY total_fare) AS p25_fare,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY total_fare) AS p75_fare,
    STDDEV(total_fare)                                AS stddev_fare,
    COUNT(*)                                          AS n_observations,
    AVG(quality_score)                                AS avg_quality
FROM fare_observations
WHERE quality_score >= 60
GROUP BY route_id, day
WITH NO DATA;

SELECT add_continuous_aggregate_policy('route_day_agg',
    start_offset => INTERVAL '3 days', end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

CREATE MATERIALIZED VIEW route_leadbucket_day_agg
WITH (timescaledb.continuous) AS
SELECT
    route_id, lead_bucket,
    time_bucket('1 day', observed_at) AS day,
    AVG(total_fare) AS mean_fare,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY total_fare) AS median_fare,
    COUNT(*) AS n_observations
FROM fare_observations
WHERE quality_score >= 60
GROUP BY route_id, lead_bucket, day
WITH NO DATA;

CREATE MATERIALIZED VIEW airline_day_agg
WITH (timescaledb.continuous) AS
SELECT
    airline_id, route_id,
    time_bucket('1 day', observed_at) AS day,
    AVG(total_fare) AS mean_fare,
    COUNT(*) AS n_observations
FROM fare_observations
WHERE quality_score >= 60
GROUP BY airline_id, route_id, day
WITH NO DATA;
```

---

## 5. Derived statistical product tables (Tier 3)

### 5.1 `index_values`

```sql
CREATE TABLE index_values (
    index_id            BIGSERIAL PRIMARY KEY,
    date                DATE NOT NULL,
    level               VARCHAR(20) NOT NULL
                             CHECK (level IN ('NATIONAL','REGIONAL','ROUTE','AIRLINE')),
    scope               VARCHAR(20) NOT NULL,      -- 'NATIONAL' | region name | route_code | airline code
    index_value         NUMERIC(8,3) NOT NULL,
    base_period         DATE NOT NULL,
    weight              NUMERIC(6,4),               -- NULL for NATIONAL

    estimator           VARCHAR(20) NOT NULL
                             CHECK (estimator IN ('MEAN','MEDIAN','TRIMMED_MEAN_10','WEIGHTED_MEDIAN')),
    mean_fare           NUMERIC(10,2),
    median_fare         NUMERIC(10,2),
    trimmed_mean_fare   NUMERIC(10,2),
    weighted_median_fare NUMERIC(10,2),

    n_observations      INTEGER NOT NULL,
    weight_set_version  VARCHAR(20),
    methodology_version VARCHAR(20) NOT NULL,
    notes                TEXT,                      -- e.g. 'route excluded: n<5, weight renormalised'
    computed_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_index_value UNIQUE (date, level, scope, methodology_version)
);
CREATE INDEX idx_index_values_lookup ON index_values(level, scope, date DESC);
```

### 5.2 `leadtime_curves`

```sql
CREATE TABLE leadtime_curves (
    curve_id            BIGSERIAL PRIMARY KEY,
    route_id            INTEGER REFERENCES routes(route_id),  -- NULL = national curve
    date                DATE NOT NULL,
    lead_bucket         VARCHAR(4) NOT NULL CHECK (lead_bucket IN ('T1','T7','T15','T30','T45')),
    avg_fare            NUMERIC(10,2) NOT NULL,
    n_observations       INTEGER NOT NULL,
    elasticity           NUMERIC(6,4),               -- OLS slope, route-level only
    last_minute_premium_pct NUMERIC(6,2),
    booking_pressure     VARCHAR(10) CHECK (booking_pressure IN ('LOW','MEDIUM','HIGH')),
    methodology_version   VARCHAR(20) NOT NULL,
    computed_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_leadtime UNIQUE (route_id, date, lead_bucket, methodology_version)
);
```

### 5.3 `volatility_metrics`

```sql
CREATE TABLE volatility_metrics (
    volatility_id        BIGSERIAL PRIMARY KEY,
    route_id             INTEGER NOT NULL REFERENCES routes(route_id),
    date                 DATE NOT NULL,
    window_days           INTEGER NOT NULL,           -- 7 or 30
    std_dev               NUMERIC(10,2),
    coefficient_of_variation NUMERIC(6,4),
    price_range_min        NUMERIC(10,2),
    price_range_max        NUMERIC(10,2),
    abnormal_move_frequency NUMERIC(5,2),
    volatility_score        VARCHAR(10) CHECK (volatility_score IN ('LOW','MEDIUM','HIGH')),
    methodology_version      VARCHAR(20) NOT NULL,
    computed_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_volatility UNIQUE (route_id, date, window_days, methodology_version)
);
```

### 5.4 `anomalies`

```sql
CREATE TABLE anomalies (
    anomaly_id           BIGSERIAL PRIMARY KEY,
    route_id             INTEGER NOT NULL REFERENCES routes(route_id),
    observation_id        BIGINT,                     -- representative triggering observation, nullable
    detected_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    fare_period_start       TIMESTAMPTZ NOT NULL,
    fare_period_end          TIMESTAMPTZ NOT NULL,

    expected_fare             NUMERIC(10,2) NOT NULL,
    observed_fare              NUMERIC(10,2) NOT NULL,
    deviation_pct                NUMERIC(6,2) NOT NULL,
    severity                      VARCHAR(10) NOT NULL
                                       CHECK (severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),

    detectors_fired                TEXT[] NOT NULL,     -- {'zscore','mad','isolation_forest'}
    anomaly_class                   VARCHAR(20) NOT NULL DEFAULT 'MARKET'
                                       CHECK (anomaly_class IN ('MARKET','SCRAPER')),

    factor_attribution               JSONB,               -- [{"factor":"weekend_demand","pct":21.0}, ...]
    attribution_note                  VARCHAR(200) NOT NULL
                                       DEFAULT 'Model-based attribution; shares are estimated, not measured.',

    status                             VARCHAR(20) NOT NULL DEFAULT 'OPEN'
                                       CHECK (status IN ('OPEN','ACKNOWLEDGED','RESOLVED','FALSE_POSITIVE')),
    model_version                       VARCHAR(20) NOT NULL,
    created_at                           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_anomalies_route_time ON anomalies(route_id, detected_at DESC);
CREATE INDEX idx_anomalies_severity   ON anomalies(severity, status);
CREATE INDEX idx_anomalies_class      ON anomalies(anomaly_class);
```

### 5.5 `forecasts`

```sql
CREATE TABLE forecasts (
    forecast_id          BIGSERIAL PRIMARY KEY,
    scope                VARCHAR(20) NOT NULL,        -- 'NATIONAL' or route_code
    forecast_date          DATE NOT NULL,               -- the date being predicted
    generated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    horizon_days               INTEGER NOT NULL,

    prediction                  NUMERIC(10,2) NOT NULL,
    lower_bound                  NUMERIC(10,2) NOT NULL,
    upper_bound                   NUMERIC(10,2) NOT NULL,
    confidence_level                NUMERIC(4,2) NOT NULL DEFAULT 0.80,
    pressure_band                    VARCHAR(10) CHECK (pressure_band IN ('LOW','MEDIUM','HIGH')),

    model_name                        VARCHAR(30) NOT NULL,   -- 'SARIMA','GRADIENT_BOOSTING', ...
    model_version                      VARCHAR(20) NOT NULL,
    validation_mape                     NUMERIC(6,3),

    CONSTRAINT chk_forecast_bounds CHECK (lower_bound <= prediction AND prediction <= upper_bound),
    CONSTRAINT uq_forecast UNIQUE (scope, forecast_date, model_version)
);
CREATE INDEX idx_forecasts_scope_date ON forecasts(scope, forecast_date);
```

### 5.6 `backtest_runs`

```sql
CREATE TABLE backtest_runs (
    backtest_id          BIGSERIAL PRIMARY KEY,
    run_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    route_scope             VARCHAR(20) NOT NULL DEFAULT 'ALL',   -- 'ALL' or route_code
    estimator                 VARCHAR(20) NOT NULL,
    train_start                DATE NOT NULL,
    train_end                    DATE NOT NULL,
    test_start                    DATE NOT NULL,
    test_end                       DATE NOT NULL,
    n_test_days                     INTEGER NOT NULL CHECK (n_test_days >= 30),

    mae                              NUMERIC(10,2),
    rmse                              NUMERIC(10,2),
    mape                               NUMERIC(6,3),
    correlation                        NUMERIC(5,4),
    directional_accuracy                 NUMERIC(5,2),

    dgca_vintage                          VARCHAR(20) NOT NULL,
    methodology_version                    VARCHAR(20) NOT NULL,
    series_json                             JSONB          -- aligned {date, ours, dgca} pairs for chart rendering
);
CREATE INDEX idx_backtest_recent ON backtest_runs(run_at DESC);
```

### 5.7 `cpi_simulations`

```sql
CREATE TABLE cpi_simulations (
    simulation_id         BIGSERIAL PRIMARY KEY,
    run_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    period_month              DATE NOT NULL,
    base_cpi                   NUMERIC(8,2) NOT NULL,
    cpi_vintage                  VARCHAR(20) NOT NULL,
    airfare_index                 NUMERIC(8,3) NOT NULL,
    airfare_weight_pct              NUMERIC(5,3) NOT NULL,
    augmented_index                  NUMERIC(8,2) NOT NULL,
    scenario_label                     VARCHAR(50),
    disclaimer                           VARCHAR(300) NOT NULL DEFAULT
        'This module is a simulation for analytical demonstration. It does not represent an official CPI revision or official NSO methodology.',
    created_by_key_id                     INTEGER REFERENCES api_keys(key_id)
);
```

---

## 6. Data quality & operational tables (Tier 5)

### 6.1 `scrape_runs`

```sql
CREATE TABLE scrape_runs (
    run_id              BIGSERIAL PRIMARY KEY,
    source_id             INTEGER NOT NULL REFERENCES sources(source_id),
    started_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at              TIMESTAMPTZ,
    records_found               INTEGER NOT NULL DEFAULT 0,
    records_valid                 INTEGER NOT NULL DEFAULT 0,
    records_failed                  INTEGER NOT NULL DEFAULT 0,
    status                            VARCHAR(20) NOT NULL DEFAULT 'RUNNING'
                                       CHECK (status IN ('RUNNING','SUCCESS','PARTIAL','FAILED','SKIPPED_ROBOTS','SKIPPED_CHALLENGE')),
    error_message                       TEXT,
    adapter_version                        VARCHAR(20) NOT NULL,
    triggered_by                             VARCHAR(20) NOT NULL DEFAULT 'SCHEDULER'
                                       CHECK (triggered_by IN ('SCHEDULER','MANUAL'))
);
CREATE INDEX idx_scrape_runs_source_time ON scrape_runs(source_id, started_at DESC);

ALTER TABLE fare_observations_raw
    ADD CONSTRAINT fk_raw_scrape_run FOREIGN KEY (scrape_run_id) REFERENCES scrape_runs(run_id);
```

### 6.2 `data_quality_flags`

```sql
CREATE TABLE data_quality_flags (
    flag_id              BIGSERIAL PRIMARY KEY,
    raised_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    scope_type                VARCHAR(20) NOT NULL CHECK (scope_type IN ('SOURCE','ROUTE','PIPELINE')),
    scope_ref                   VARCHAR(50) NOT NULL,     -- source_code or route_code
    flag_type                     VARCHAR(40) NOT NULL,    -- 'SOURCE_DOWN','DUPLICATE_FLOOD','TAX_MISMATCH', ...
    severity                        VARCHAR(10) NOT NULL CHECK (severity IN ('INFO','WARNING','CRITICAL')),
    description                       TEXT NOT NULL,
    resolved_at                        TIMESTAMPTZ,
    resolution_note                      TEXT
);
CREATE INDEX idx_dq_flags_open ON data_quality_flags(scope_type, scope_ref) WHERE resolved_at IS NULL;
```

### 6.3 `api_keys`

```sql
CREATE TABLE api_keys (
    key_id                BIGSERIAL PRIMARY KEY,
    key_prefix              VARCHAR(12) NOT NULL UNIQUE,   -- shown to user, used for lookup
    key_hash                  VARCHAR(200) NOT NULL,        -- Argon2 hash, never the raw key
    owner_name                  VARCHAR(150) NOT NULL,
    owner_org                     VARCHAR(150),
    role                             VARCHAR(20) NOT NULL DEFAULT 'PUBLIC'
                                       CHECK (role IN ('PUBLIC','ANALYST','ADMIN')),
    rate_limit_per_min                 INTEGER NOT NULL DEFAULT 60,
    daily_quota                          INTEGER NOT NULL DEFAULT 10000,
    is_active                              BOOLEAN NOT NULL DEFAULT TRUE,
    created_at                               TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_used_at                               TIMESTAMPTZ,
    expires_at                                   TIMESTAMPTZ
);
```

### 6.4 `audit_log`

```sql
CREATE TABLE audit_log (
    audit_id              BIGSERIAL PRIMARY KEY,
    occurred_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor_key_id                INTEGER REFERENCES api_keys(key_id),
    action                         VARCHAR(60) NOT NULL,   -- 'WEIGHT_SET_PUBLISHED','METHODOLOGY_BUMPED','MANUAL_SCRAPE_TRIGGERED'
    target_type                      VARCHAR(30),
    target_ref                          VARCHAR(50),
    detail                                 JSONB,
    ip_address                              INET
);
CREATE INDEX idx_audit_log_time ON audit_log(occurred_at DESC);
```

---

## 7. Enumerations summary

| Domain | Values |
|---|---|
| `region` | NORTH, SOUTH, EAST, WEST, NORTHEAST, CENTRAL |
| `source_type` | AIRLINE_DIRECT, OTA |
| `source.status` | ACTIVE, DEGRADED, UNAVAILABLE, DISABLED |
| `lead_bucket` | T1, T7, T15, T30, T45 |
| `fare_class` | ECONOMY, PREMIUM_ECONOMY, BUSINESS |
| `availability_status` | AVAILABLE, LIMITED, SOLD_OUT, UNKNOWN |
| `quality_band` | HIGH (>=85), MEDIUM (60-84), LOW (<60) |
| `index.level` | NATIONAL, REGIONAL, ROUTE, AIRLINE |
| `estimator` | MEAN, MEDIAN, TRIMMED_MEAN_10, WEIGHTED_MEDIAN |
| `severity` (anomaly) | LOW, MEDIUM, HIGH, CRITICAL |
| `anomaly.status` | OPEN, ACKNOWLEDGED, RESOLVED, FALSE_POSITIVE |
| `anomaly_class` | MARKET, SCRAPER |
| `volatility_score` | LOW, MEDIUM, HIGH |
| `pressure_band` | LOW, MEDIUM, HIGH |
| `scrape_run.status` | RUNNING, SUCCESS, PARTIAL, FAILED, SKIPPED_ROBOTS, SKIPPED_CHALLENGE |
| `api_key.role` | PUBLIC, ANALYST, ADMIN |
| `data_quality_flags.scope_type` | SOURCE, ROUTE, PIPELINE |

---

## 8. Data lifecycle & retention

| Table | Retention policy |
|---|---|
| `fare_observations_raw` | Compressed after 30 days; JSONB payload nulled after 180 days (row/columns kept for count integrity) |
| `fare_observations` | Compressed after 30 days; retained indefinitely (small footprint per row) |
| `index_values`, `anomalies`, `forecasts` | Retained indefinitely — these are the published statistical products |
| `scrape_runs` | Retained 1 year, then aggregated into monthly reliability summaries |
| `audit_log` | Retained indefinitely (compliance) |
| `data_quality_flags` | Retained indefinitely; resolved flags kept for historical analysis |

---

## 9. Migration strategy

- **Alembic** manages schema migrations; one migration per logical change, reviewed like code.
- Every migration that changes a column feeding index/forecast/anomaly math is paired with a **methodology_version bump** recorded in `methodology_versions` (a small lookup table — see below) so historical values remain interpretable under the version that produced them.
- Hypertable and continuous-aggregate DDL lives in dedicated migration files (TimescaleDB DDL is not always auto-generatable by Alembic's autogenerate, so these are hand-written and reviewed).

```sql
CREATE TABLE methodology_versions (
    version             VARCHAR(20) PRIMARY KEY,     -- 'idx-1.2.0'
    published_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    description               TEXT NOT NULL,
    estimator_default            VARCHAR(20) NOT NULL,
    quality_threshold               NUMERIC(5,2) NOT NULL DEFAULT 60,
    min_observations_per_period       INTEGER NOT NULL DEFAULT 5,
    changelog                            TEXT
);
```

---

## 10. Seed data (demo resilience)

`backend/seeds/` produces a deterministic dataset (fixed RNG seed) covering:

- 15 basket routes across all four regions, 5 airlines, 3 OTAs, 1 airline-direct channel.
- 45 days of history at all 5 lead-time buckets, including one clear injected anomaly on `DEL-BOM`.
- A DGCA benchmark series aligned to the same window (90 days, satisfying the 30-day minimum with margin).
- One CPI reference vintage (`cpi-2024-base`) plus one legacy vintage (`cpi-2012-base`) to demonstrate vintage labelling.
- Pre-computed `index_values`, `leadtime_curves`, `anomalies`, `forecasts` and one `backtest_runs` row, so every screen renders meaningfully immediately after `make seed`, with `data_mode = REPLAY`.

---

## 11. API contract (backend surface, maps to the schema above)

Base path: `/api/v1`. All responses use the envelope from [02-ARCHITECTURE.md §5.3](02-ARCHITECTURE.md#53-response-envelope).

| Method & path | Backing tables | Notes |
|---|---|---|
| `GET /index` | `index_values` | `?level=&scope=&from=&to=&granularity=` |
| `GET /index/route/{route_code}` | `index_values`, `routes` | Route-level index series |
| `GET /index/methodology` | `methodology_versions`, `route_weights` | Current formula, estimator, weights |
| `GET /fares` | `fare_observations` (+ `_raw` if `?raw=true`) | Paginated, heavily filterable, `analyst`+ only for raw |
| `GET /routes` | `routes`, `route_weights`, `airports` | Master + current weights |
| `GET /airlines` | `airlines` | Master |
| `GET /lead-time` | `leadtime_curves` | `?route=&from=&to=` |
| `GET /anomalies` | `anomalies` | `?severity=&status=&route=&class=` |
| `GET /anomalies/{id}` | `anomalies`, `fare_observations` | Full detail incl. factor attribution |
| `GET /volatility` | `volatility_metrics` | `?route=&window=` |
| `GET /divergence` | `fare_observations` (aggregated) | Source-to-source spread for an itinerary |
| `GET /forecast` | `forecasts` | `?scope=&horizon=`; response always includes bounds |
| `GET /backtest` | `backtest_runs` | Latest run by default; `?id=` for a specific run |
| `GET /cpi-simulation` | `cpi_simulations`, `cpi_reference`, `index_values` | `?weight=&period=`; response always includes `disclaimer` |
| `POST /cpi-simulation` | `cpi_simulations` | `analyst`+; persists a named scenario |
| `GET /data-quality` | `data_quality_flags`, `sources`, `scrape_runs` | Collection health board |
| `GET /events` | `events` | Calendar |
| `POST /admin/collection/trigger` | `scrape_runs` | `admin` only, manual source trigger |
| `POST /admin/weights` | `route_weights` | `admin` only, publishes a new `weight_set_version` |
| `GET /admin/audit-log` | `audit_log` | `admin` only |

Every `GET` endpoint supports `page`, `page_size` (max 500), and returns `meta.data_mode` (`LIVE` / `CACHED` / `REPLAY`) so the frontend can render the honesty badge described in the design document.
