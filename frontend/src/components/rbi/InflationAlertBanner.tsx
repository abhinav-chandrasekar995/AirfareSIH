"use client";
import { AlertTriangle, Download } from "lucide-react";
import { istDate } from "@/lib/format";
import type { ApixAlert } from "@/types/api";

// Reads the live /apix/alert status. Two states, not a dismissible toast - a policy
// alert that can be clicked away defeats the point. See RBI_APIX_MODULE_LOG.md §2.
export function InflationAlertBanner({ alert }: { alert: ApixAlert }) {
  if (!alert.triggered) {
    return (
      <div
        role="status"
        className="flex items-center gap-2.5 rounded-md border border-border-subtle bg-panel-alt px-4 py-3 text-secondary mb-4"
      >
        <span className="h-2 w-2 rounded-full shrink-0" style={{ background: "var(--up-600)" }} aria-hidden />
        <p className="text-xs font-medium">
          <strong className="uppercase tracking-wide mr-1">Normal.</strong>
          Core APIx is within RBI tolerance bands as of {istDate(alert.as_of)}.
        </p>
      </div>
    );
  }

  return (
    <div
      role="alert"
      className="flex items-start gap-2.5 rounded-md border px-4 py-3 mb-4 flex-wrap"
      style={{ borderColor: "var(--signal-600)", background: "var(--signal-100)", color: "var(--signal-700)" }}
    >
      <AlertTriangle size={16} className="mt-0.5 shrink-0" aria-hidden />
      <p className="text-xs font-medium leading-relaxed flex-1 min-w-[200px]">
        <strong className="uppercase tracking-wide mr-1">High inflation risk.</strong>
        {alert.message}
      </p>
      <a
        href="/backend/api/v1/reports/rbi-policy-brief"
        className="inline-flex items-center gap-1.5 shrink-0 text-[11px] font-bold uppercase tracking-wide rounded-md px-2.5 py-1.5 text-white hover:opacity-90"
        style={{ background: "var(--signal-600)" }}
      >
        <Download size={12} /> Generate RBI Policy Brief
      </a>
    </div>
  );
}
