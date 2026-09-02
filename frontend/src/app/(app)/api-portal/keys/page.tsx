"use client";
import { useState } from "react";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { EmptyState } from "@/components/panels/EmptyState";

export default function ApiKeysPage() {
  const [key, setKey] = useState("");
  const [saved, setSaved] = useState(false);

  const save = () => {
    if (typeof window !== "undefined" && key.trim()) {
      window.localStorage.setItem("iai_api_key", key.trim());
      setSaved(true);
    }
  };

  return (
    <div>
      <Breadcrumbs items={[{ label: "Home", href: "/dashboard" }, { label: "API Portal", href: "/api-portal" }, { label: "API Keys" }]} />
      <PageHeader title="API Keys" subtitle="Keys are ADMIN-created on the backend during seed load and shown once in the terminal" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <PanelShell title="Use a Key in This Browser" source="local storage (not sent anywhere but the API)">
          <p className="text-xs text-secondary mb-3">
            Paste a demo key (printed once by <code className="mono text-[11px]">python -m seeds.load_seed</code>) to
            authenticate requests from this browser as ANALYST or ADMIN.
          </p>
          <div className="flex gap-2">
            <input
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="iai_xxxxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              className="flex-1 text-xs bg-panel border border-border-subtle rounded-md px-2 py-1.5 mono"
            />
            <button onClick={save} className="text-xs bg-interactive text-white px-3 py-1.5 rounded-md hover:bg-interactive-hover">Save</button>
          </div>
          {saved && <p className="text-[11px] text-quality-high mt-2">Key saved for this browser.</p>}
        </PanelShell>

        <PanelShell title="Roles" source="api_keys">
          <table className="w-full text-xs">
            <tbody>
              <tr className="border-b border-border-subtle"><td className="py-1.5 font-medium">PUBLIC</td><td className="py-1.5 text-muted">Read national/regional index, routes, airlines. Heavily rate-limited.</td></tr>
              <tr className="border-b border-border-subtle"><td className="py-1.5 font-medium">ANALYST</td><td className="py-1.5 text-muted">All read endpoints, raw observation export, backtest configuration.</td></tr>
              <tr><td className="py-1.5 font-medium">ADMIN</td><td className="py-1.5 text-muted">Trigger collection, publish weights, view the audit log.</td></tr>
            </tbody>
          </table>
        </PanelShell>
      </div>
    </div>
  );
}
