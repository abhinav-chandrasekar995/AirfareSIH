"use client";
import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { KpiCard } from "@/components/kpi/KpiCard";
import { ScenarioSlider } from "@/components/cpi/ScenarioSlider";
import { SensitivityChart } from "@/components/charts/SensitivityChart";
import { Skeleton, ErrorState } from "@/components/panels/EmptyState";
import { useCpiSimulation } from "@/lib/api/hooks";
import { num } from "@/lib/format";

// NOTE (user-directed deviation, logged in IMPLEMENTATION_LOG.md): the disclaimer
// banner, formula text and Methodology/Backtesting/Airfare Index links were removed
// from this page on explicit request. The disclaimer is still returned by the backend
// in every /cpi-simulation API response (`envelope.disclaimer`) and enforced by
// CpiDisclaimerMiddleware - only the UI-visible banner on this page was removed.
export default function CpiSimulatorPage() {
  const [weight, setWeight] = useState(2.5);
  const { data, isLoading, isError, error } = useCpiSimulation(weight);

  return (
    <div>
      <PageHeader title="CPI Augmentation Simulator" subtitle="Scenario-weighted augmentation of the existing CPI with the airfare signal" />

      {isLoading ? (
        <Skeleton className="h-96" />
      ) : isError || !data ? (
        <ErrorState message={error instanceof Error ? error.message : "CPI reference data has not been ingested."} />
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
            <KpiCard label="Base CPI" value={num(data.data.base_cpi, 1)} context={`${data.data.cpi_vintage} (${data.data.cpi_base_year})`} />
            <KpiCard label="Airfare Index" value={num(data.data.airfare_index, 1)} context="our index" />
            <KpiCard label="Airfare Weight" value={`${data.data.airfare_weight_pct.toFixed(1)}%`} />
            <KpiCard label="Simulated Augmented Index" value={num(data.data.augmented_index, 1)} delta={data.data.delta} deltaBasis="vs base" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <PanelShell title="Scenario Control" source="cpi_simulations">
              <ScenarioSlider value={weight} onChange={setWeight} />
              <div className="mt-6 space-y-2 text-xs">
                {["Existing CPI", "Airfare signal", "Scenario weighting", "Simulated augmented measurement"].map((step, i, arr) => (
                  <div key={step} className="flex items-center gap-2">
                    <span className="h-5 w-5 rounded-full bg-panel-alt text-[10px] flex items-center justify-center font-semibold shrink-0">{i + 1}</span>
                    <span className="text-secondary">{step}</span>
                    {i < arr.length - 1 && <span className="text-muted ml-auto" aria-hidden>↓</span>}
                  </div>
                ))}
              </div>
            </PanelShell>

            <PanelShell title="Sensitivity" subtitle="How the result changes as the weight varies" source="cpi simulation">
              <SensitivityChart points={data.data.sensitivity} currentWeight={weight} />
            </PanelShell>
          </div>
        </>
      )}
    </div>
  );
}
