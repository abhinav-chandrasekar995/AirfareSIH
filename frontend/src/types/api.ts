// Response types mirroring the backend Pydantic schemas.

export interface Airline {
  airline_code: string; name: string; airline_type: string; is_active: boolean;
}

export interface IndexPoint {
  date: string; level: string; scope: string; index_value: number;
  n_observations: number; estimator: string; weight: number | null; notes: string | null;
}

// RBI APIx module (/api/v1/apix/*) - narrower point shape than IndexPoint since
// apix_service._to_point() doesn't carry estimator/weight/notes. See RBI_APIX_MODULE_LOG.md.
export interface ApixPoint {
  date: string; level: string; scope: string; index_value: number; n_observations: number;
}

export interface ApixComparison {
  core: ApixPoint[];
  headline: ApixPoint[];
}

export interface PriceBreakdown {
  scope: string;
  scope_level: string;
  as_of: string;
  avg_base_fare: number | null;
  avg_taxes_and_fees: number | null;
  avg_total_fare: number | null;
  n_observations: number;
}

export interface ApixAlert {
  triggered: boolean;
  status: string;
  scope: string;
  scope_level: string;
  scope_wow_pct: number | null;
  scope_threshold_pct: number;
  national_wow_pct: number | null;
  national_threshold_pct: number;
  spiking_route: string | null;
  spiking_route_wow_pct: number | null;
  route_threshold_pct: number;
  message: string | null;
  as_of: string | null;
}

export interface IndexSummary {
  scope: string; level: string; current_value: number; previous_value: number | null;
  change_pct: number | null; change_direction: string; base_period: string;
  as_of: string; n_observations: number;
}

export interface Mover {
  route_code: string; origin_city: string; destination_city: string;
  current_fare: number; change_pct: number; direction: string;
}

export interface Insight {
  id: string; text: string; severity: string; href: string | null; metric: number | null;
}

export interface PressurePoint {
  route_code: string; origin: string; destination: string;
  origin_lat: number; origin_lon: number; destination_lat: number; destination_lon: number;
  origin_city: string; destination_city: string; region: string;
  index_value: number; pressure: string;
}

export interface Dashboard {
  index_value: number | null; index_change_mom_pct: number | null;
  routes_tracked: number; airlines_tracked: number; ota_sources: number;
  flights_monitored: number; total_data_points: number;
  base_period: string; as_of: string | null;
  top_increases: Mover[]; top_decreases: Mover[];
  insights: Insight[]; pressure_map: PressurePoint[];
}

export interface RouteSummary {
  route_code: string; origin: string; destination: string; origin_city: string;
  destination_city: string; region: string; distance_km: number | null; in_basket: boolean;
  weight: number | null; current_fare: number | null; route_index: number | null;
  n_observations: number; volatility_score: string | null;
}

export interface TrendPoint { date: string; value: number; n_observations: number | null; }

export interface RouteDetail {
  route_code: string; origin: string; destination: string; origin_city: string;
  destination_city: string; origin_airport: string; destination_airport: string;
  region: string; distance_km: number | null; in_basket: boolean; weight: number | null;
  route_index: number | null; current_fare: number | null; avg_7d: number | null;
  avg_30d: number | null; avg_yearly: number | null; change_mom_pct: number | null;
  n_observations: number; trend: TrendPoint[];
  airlines: { airline_code: string; airline: string; median_fare: number; n_observations: number }[];
  sources: SourceDivergence[];
  composition: Record<string, number> | null;
  volatility: { std_dev: number; coefficient_of_variation: number; volatility_score: string; abnormal_move_frequency: number } | null;
}

export interface SourceDivergence {
  source: string; source_code: string; source_type: string; avg_fare: number;
  vs_direct_pct: number | null; avg_convenience_fee: number; n_observations: number;
}

export interface LeadTimePoint {
  lead_bucket: string; lead_days: number; avg_fare: number;
  n_observations: number; vs_earliest_pct: number | null;
}

export interface LeadTime {
  route_code: string | null; curve: LeadTimePoint[]; elasticity: number | null;
  last_minute_premium_pct: number | null; early_booking_advantage_pct: number | null;
  booking_pressure: string | null; method_note: string;
  by_route: { route_code: string; elasticity: number | null; last_minute_premium_pct: number | null; booking_pressure: string | null }[];
}

export interface Factor { factor: string; label: string; pct: number; }

export interface Anomaly {
  anomaly_id: number; route_code: string; origin_city: string; destination_city: string;
  detected_at: string; expected_fare: number; observed_fare: number; deviation_pct: number;
  severity: string; anomaly_class: string; lead_bucket: string | null;
  detectors_fired: string[]; factor_attribution: Factor[]; attribution_note: string;
  status: string; model_version: string;
}

export interface ForecastPoint { forecast_date: string; prediction: number; lower_bound: number; upper_bound: number; }

export interface Forecast {
  scope: string; horizon_days: number; confidence_level: number; pressure_band: string;
  forecast_range: number[]; points: ForecastPoint[]; model_name: string; model_version: string;
  model_comparison: { model_name: string; validation_mape: number; validation_rmse: number; selected: boolean }[];
}

export interface Backtest {
  backtest_id: number; run_at: string; route_scope: string; estimator: string;
  train_start: string; train_end: string; test_start: string; test_end: string;
  n_test_days: number; mae: number | null; rmse: number | null; mape: number | null;
  correlation: number | null; directional_accuracy: number | null;
  dgca_vintage: string; alignment_method: string;
  series: { month: string; ours: number; dgca: number }[];
}

export interface MospiComparisonPoint {
  month: string; official_index: number | null; nowcast_index: number; is_official: boolean;
}

// Real MoSPI Airfare CPI vs our own rebased Headline APIx - genuinely independent
// benchmark, unlike Backtest above (whose "dgca" series is synthetic). See
// backend/app/services/mospi_service.py and IMPLEMENTATION_LOG.md.
export interface MospiComparison {
  series_vintage: string; base_year: string; anchor_month: string; scale_factor: number;
  alignment_method: string;
  points: MospiComparisonPoint[];
  overlap_months: number;
  overlap_metrics: {
    mae: number; rmse: number; mape: number; correlation: number; directional_accuracy: number;
  } | null;
  last_official_month: string; latest_nowcast_month: string | null; data_lag_days: number;
}

export interface CpiSimulation {
  period_month: string; base_cpi: number; cpi_vintage: string; cpi_base_year: string;
  airfare_index: number; airfare_weight_pct: number; augmented_index: number;
  delta: number; formula: string;
  sensitivity: { weight_pct: number; augmented_index: number; delta: number }[];
}

export interface Volatility {
  route_code: string; date: string; window_days: number; std_dev: number | null;
  coefficient_of_variation: number | null; price_range_min: number | null;
  price_range_max: number | null; abnormal_move_frequency: number | null; volatility_score: string | null;
}

export interface SourceHealth {
  source_code: string; source_name: string; source_type: string; status: string;
  reliability_score: number; last_run_at: string | null; records_found: number;
  records_valid: number; records_failed: number; success_rate: number;
  latency_ms: number | null; rate_limit_rpm: number;
}

export interface QualityFlag {
  flag_id: number; raised_at: string; scope_type: string; scope_ref: string;
  flag_type: string; severity: string; description: string; resolved_at: string | null;
}

export interface DataQuality {
  sources: SourceHealth[]; flags: QualityFlag[];
  recent_runs: { run_id: number; source_id: number; started_at: string; status: string;
    records_found: number; records_valid: number; records_failed: number;
    latency_ms: number | null; triggered_by: string; error_message: string | null }[];
}

export interface Methodology {
  methodology_version: string; base_period: string; estimator: string;
  quality_threshold: number; min_observations_per_period: number;
  weight_set_version: string | null; weight_source: string | null;
  route_index_formula: string; aggregate_formula: string; missing_route_policy: string;
  basket_size: number; weights: { route_code: string; weight: number; source: string }[];
}

export interface FareObservation {
  observation_id: number; observed_at: string; route_code: string; origin: string;
  destination: string; airline: string; airline_code: string; flight_number: string;
  departure_datetime: string; lead_days: number; lead_bucket: string; fare_class: string;
  base_fare: number; taxes: number; udf: number; airport_charges: number;
  convenience_fee: number; total_fare: number; source: string; source_type: string;
  seats_available: number | null; availability_status: string; is_outlier: boolean;
  imputed_fields: string[]; quality_score: number; quality_band: string;
}
