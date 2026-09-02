"use client";
import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { useRoutes } from "@/lib/api/hooks";
import { Download, FileText } from "lucide-react";

// Each report is a real GET to a backend endpoint that assembles CSV from the same
// service layer the interactive pages call (see backend/app/api/v1/routers/reports.py)
// - not a disabled placeholder. "Route Intelligence Brief" needs a route selected
// first; the others need no extra input and download immediately.
const REPORT_TYPES = [
  {
    name: "Weekly Index Summary",
    desc: "National + regional index movement, top movers, key insights.",
    path: "/reports/index-summary",
    needsRoute: false,
  },
  {
    name: "Route Intelligence Brief",
    desc: "Fare trend, composition and volatility for a selected route.",
    path: "/reports/route-brief",
    needsRoute: true,
  },
  {
    name: "Backtesting Validation Report",
    desc: "DGCA benchmark comparison with full error metrics.",
    path: "/reports/backtest-validation",
    needsRoute: false,
  },
  {
    name: "CPI Augmentation Scenario Note",
    desc: "Simulation output with the mandatory disclaimer and formula.",
    path: "/reports/cpi-scenario",
    needsRoute: false,
  },
];

export default function ReportsPage() {
  const { data: routes } = useRoutes();
  const [selectedRoute, setSelectedRoute] = useState("");

  return (
    <div>
      <PageHeader title="Reports" subtitle="CSV reports generated from live data, for policy and research audiences" />
      <PanelShell title="Available Report Templates" source="reports">
        <ul className="divide-y divide-border-subtle">
          {REPORT_TYPES.map((r) => {
            const url = r.needsRoute
              ? `/backend/api/v1${r.path}?route_code=${selectedRoute}`
              : `/backend/api/v1${r.path}`;
            const disabled = r.needsRoute && !selectedRoute;

            return (
              <li key={r.name} className="flex items-center justify-between gap-4 py-3 flex-wrap">
                <div className="flex items-start gap-2.5 min-w-0">
                  <FileText size={16} className="text-muted mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-primary">{r.name}</div>
                    <div className="text-xs text-muted">{r.desc}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {r.needsRoute && (
                    <select
                      value={selectedRoute}
                      onChange={(e) => setSelectedRoute(e.target.value)}
                      className="text-xs bg-panel border border-border-subtle rounded-md px-2 py-1.5"
                      aria-label="Route for Route Intelligence Brief"
                    >
                      <option value="">Select a route…</option>
                      {routes?.data.map((route) => (
                        <option key={route.route_code} value={route.route_code}>{route.route_code}</option>
                      ))}
                    </select>
                  )}
                  {disabled ? (
                    <button
                      disabled
                      className="inline-flex items-center gap-1.5 text-xs border border-border-subtle rounded-md px-3 py-1.5 text-muted opacity-50"
                      title="Select a route first"
                    >
                      <Download size={13} /> Generate
                    </button>
                  ) : (
                    <a
                      href={url}
                      className="inline-flex items-center gap-1.5 text-xs bg-interactive text-white rounded-md px-3 py-1.5 hover:bg-interactive-hover"
                    >
                      <Download size={13} /> Generate
                    </a>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </PanelShell>
    </div>
  );
}
