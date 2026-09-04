"use client";
import { useQuery } from "@tanstack/react-query";
import { apiGet, type Envelope } from "./client";
import type {
  Airline, Anomaly, ApixAlert, ApixComparison, Backtest, CpiSimulation, Dashboard, DataQuality,
  Forecast, IndexPoint, IndexSummary, LeadTime, Methodology, MospiComparison, PriceBreakdown,
  RouteDetail, RouteSummary, Volatility, FareObservation,
} from "@/types/api";

const STALE = 60_000;

export function useDashboard() {
  return useQuery({ queryKey: ["dashboard"], queryFn: () => apiGet<Dashboard>("/dashboard"), staleTime: STALE });
}

export function useAirlines() {
  return useQuery({ queryKey: ["airlines"], queryFn: () => apiGet<Airline[]>("/airlines"), staleTime: STALE });
}

export function useIndexSeries(level = "NATIONAL", scope?: string) {
  return useQuery({
    queryKey: ["index", level, scope],
    queryFn: () => apiGet<IndexPoint[]>("/index", { level, scope }),
    staleTime: STALE,
  });
}

export function useIndexSummary() {
  return useQuery({
    queryKey: ["index-summary"],
    queryFn: () => apiGet<{ headline: IndexSummary | null; regional: IndexSummary[] }>("/index/summary"),
    staleTime: STALE,
  });
}

export function useMethodology() {
  return useQuery({ queryKey: ["methodology"], queryFn: () => apiGet<Methodology>("/index/methodology"), staleTime: STALE });
}

export function useRoutes() {
  return useQuery({ queryKey: ["routes"], queryFn: () => apiGet<RouteSummary[]>("/routes"), staleTime: STALE });
}

export function useRoute(code: string) {
  return useQuery({
    queryKey: ["route", code],
    queryFn: () => apiGet<RouteDetail>(`/routes/${code}`),
    staleTime: STALE,
    enabled: Boolean(code),
  });
}

export function useLeadTime(route?: string) {
  return useQuery({ queryKey: ["lead-time", route], queryFn: () => apiGet<LeadTime>("/lead-time", { route }), staleTime: STALE });
}

export function useAnomalies(params: Record<string, string | number | undefined> = {}) {
  return useQuery({ queryKey: ["anomalies", params], queryFn: () => apiGet<Anomaly[]>("/anomalies", params), staleTime: STALE });
}

export function useAnomaly(id: number) {
  return useQuery({ queryKey: ["anomaly", id], queryFn: () => apiGet<Anomaly>(`/anomalies/${id}`), enabled: Boolean(id) });
}

export function useForecast(scope = "NATIONAL") {
  return useQuery({ queryKey: ["forecast", scope], queryFn: () => apiGet<Forecast>("/forecast", { scope }), staleTime: STALE });
}

export function useBacktest() {
  return useQuery({ queryKey: ["backtest"], queryFn: () => apiGet<Backtest>("/backtest"), staleTime: STALE });
}

export function useMospiComparison() {
  return useQuery({
    queryKey: ["mospi-comparison"],
    queryFn: () => apiGet<MospiComparison>("/backtest/mospi-comparison"),
    staleTime: STALE,
  });
}

export function useCpiSimulation(weight?: number, vintage?: string) {
  return useQuery({
    queryKey: ["cpi", weight, vintage],
    queryFn: () => apiGet<CpiSimulation>("/cpi-simulation", { weight, vintage }),
    staleTime: STALE,
  });
}

export function useVolatility(route?: string) {
  return useQuery({ queryKey: ["volatility", route], queryFn: () => apiGet<Volatility[]>("/volatility", { route }), staleTime: STALE });
}

export function useDataQuality() {
  return useQuery({ queryKey: ["data-quality"], queryFn: () => apiGet<DataQuality>("/data-quality"), staleTime: STALE });
}

export function useFares(params: Record<string, string | number | undefined> = {}) {
  return useQuery({ queryKey: ["fares", params], queryFn: () => apiGet<FareObservation[]>("/fares", params), staleTime: STALE });
}

// RBI APIx module - shorter staleTime than STALE (30s vs 60s) since the alert banner
// is the one thing on the site meant to feel "live."
const APIX_STALE = 30_000;

export function useApixComparison(level = "NATIONAL", scope?: string) {
  return useQuery({
    queryKey: ["apix-comparison", level, scope],
    queryFn: () => apiGet<ApixComparison>("/apix/comparison", { level, scope }),
    staleTime: APIX_STALE,
  });
}

export function usePriceBreakdown(level = "NATIONAL", scope?: string) {
  return useQuery({
    queryKey: ["apix-price-breakdown", level, scope],
    queryFn: () => apiGet<PriceBreakdown>("/apix/price-breakdown", { level, scope }),
    staleTime: APIX_STALE,
  });
}

export function useApixAlert(level = "NATIONAL", scope?: string) {
  return useQuery({
    queryKey: ["apix-alert", level, scope],
    queryFn: () => apiGet<ApixAlert>("/apix/alert", { level, scope }),
    staleTime: APIX_STALE,
    refetchInterval: APIX_STALE,
  });
}

export type { Envelope };
