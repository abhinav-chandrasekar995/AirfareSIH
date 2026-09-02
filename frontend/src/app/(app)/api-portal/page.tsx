"use client";
import { useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { backendUrl } from "@/lib/api/client";
import { Copy } from "lucide-react";

const ENDPOINTS = [
  { method: "GET", path: "/api/v1/index", desc: "National + regional index series" },
  { method: "GET", path: "/api/v1/index/route/{route_code}", desc: "Route index series, e.g. DEL-BOM" },
  { method: "GET", path: "/api/v1/index/methodology", desc: "Formula, estimator, weights" },
  { method: "GET", path: "/api/v1/fares", desc: "Filtered fare observations (paginated)" },
  { method: "GET", path: "/api/v1/anomalies", desc: "Detected anomalies" },
  { method: "GET", path: "/api/v1/forecast", desc: "Forecast with prediction intervals" },
  { method: "GET", path: "/api/v1/routes", desc: "Route master + weights" },
  { method: "GET", path: "/api/v1/airlines", desc: "Airline master" },
  { method: "GET", path: "/api/v1/lead-time", desc: "Lead-time curve and elasticity" },
  { method: "GET", path: "/api/v1/cpi-simulation", desc: "CPI augmentation simulation" },
  { method: "GET", path: "/api/v1/backtest", desc: "DGCA back-test metrics and series" },
  { method: "GET", path: "/api/v1/data-quality", desc: "Collection health and quality flags" },
];

export default function ApiPortalPage() {
  const [selected, setSelected] = useState(ENDPOINTS[0]);
  const [copied, setCopied] = useState(false);

  const example = `curl -H "X-API-Key: YOUR_KEY" \\\n  "${backendUrl(selected.path)}"`;

  const copy = () => {
    navigator.clipboard.writeText(example);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div>
      <PageHeader
        title="API Portal"
        subtitle="REST API for NSO, RBI and research consumption — versioned, authenticated, rate-limited"
        actions={<Link href="/api-portal/keys" className="text-xs text-accent hover:underline">Manage API keys →</Link>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-4">
          <PanelShell title="Endpoints" source="OpenAPI schema" count={ENDPOINTS.length}>
            <ul className="divide-y divide-border-subtle -mx-4">
              {ENDPOINTS.map((e) => (
                <li key={e.path}>
                  <button
                    onClick={() => setSelected(e)}
                    className={`w-full text-left px-4 py-2 text-xs hover:bg-panel-alt ${selected.path === e.path ? "bg-panel-alt" : ""}`}
                  >
                    <span className="mono text-[10px] bg-[var(--up-100)] text-[var(--up-700)] px-1 py-0.5 rounded-sm mr-2">{e.method}</span>
                    <span className="mono">{e.path}</span>
                  </button>
                </li>
              ))}
            </ul>
          </PanelShell>
        </div>

        <div className="lg:col-span-8">
          <PanelShell title={selected.path} subtitle={selected.desc} source="app.api.v1.routers">
            <div className="mb-4">
              <div className="eyebrow mb-1.5">Try it</div>
              <div className="relative">
                <pre className="bg-inset rounded-md p-3 text-[11px] mono overflow-x-auto">{example}</pre>
                <button onClick={copy} className="absolute top-2 right-2 p-1.5 rounded-md bg-panel border border-border-subtle hover:bg-panel-alt" aria-label="Copy example">
                  <Copy size={12} />
                </button>
              </div>
              {copied && <span className="text-[11px] text-quality-high">Copied</span>}
            </div>
            <div className="mb-2">
              <div className="eyebrow mb-1.5">Response envelope</div>
              <pre className="bg-inset rounded-md p-3 text-[11px] mono overflow-x-auto">{`{
  "data": { ... },
  "meta": {
    "count": 0, "page": 1, "page_size": 100,
    "data_mode": "REPLAY", "quality_threshold": 60
  },
  "methodology_version": "idx-1.0.0",
  "disclaimer": null
}`}</pre>
            </div>
            <a href={backendUrl("/api/docs")} target="_blank" rel="noreferrer" className="text-xs text-accent hover:underline">Full OpenAPI documentation →</a>
          </PanelShell>
        </div>
      </div>
    </div>
  );
}
