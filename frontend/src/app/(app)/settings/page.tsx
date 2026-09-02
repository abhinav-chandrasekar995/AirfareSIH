"use client";
import { PageHeader } from "@/components/layout/PageHeader";
import { PanelShell } from "@/components/panels/PanelShell";
import { useUiStore } from "@/lib/store/uiStore";
import { useMethodology } from "@/lib/api/hooks";

export default function SettingsPage() {
  const { theme, setTheme } = useUiStore();
  const { data } = useMethodology();

  return (
    <div>
      <PageHeader title="Settings" subtitle="Display preferences and platform configuration" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <PanelShell title="Appearance" source="local preference">
          <div className="flex items-center justify-between">
            <span className="text-xs text-secondary">Theme</span>
            <div className="flex rounded-md border border-border-subtle overflow-hidden text-xs">
              <button onClick={() => setTheme("dark")} className={`px-3 py-1.5 ${theme === "dark" ? "bg-interactive text-white" : "bg-panel text-secondary"}`}>Dark</button>
              <button onClick={() => setTheme("light")} className={`px-3 py-1.5 ${theme === "light" ? "bg-interactive text-white" : "bg-panel text-secondary"}`}>Light</button>
            </div>
          </div>
        </PanelShell>

        <PanelShell title="Platform Configuration" source="methodology_versions (read-only)">
          <dl className="text-xs space-y-2">
            <div className="flex justify-between border-b border-border-subtle py-1.5"><dt className="text-muted">Methodology version</dt><dd className="numeric">{data?.data.methodology_version ?? "—"}</dd></div>
            <div className="flex justify-between border-b border-border-subtle py-1.5"><dt className="text-muted">Quality threshold</dt><dd className="numeric">≥ {data?.data.quality_threshold ?? "—"}</dd></div>
            <div className="flex justify-between py-1.5"><dt className="text-muted">Default estimator</dt><dd className="numeric">{data?.data.estimator ?? "—"}</dd></div>
          </dl>
          <p className="text-[11px] text-muted mt-3">Statistical configuration is versioned and changed only through a published methodology update, not through this page.</p>
        </PanelShell>
      </div>
    </div>
  );
}
