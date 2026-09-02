import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";

export const metadata: Metadata = {
  title: "Methodology",
  description:
    "How the India Airfare Price Index is constructed: representative route basket, DGCA-weighted aggregation, robust estimators, quality scoring, and validation against DGCA benchmarks.",
  alternates: { canonical: "/methodology" },
};

// Content preserved verbatim from the original page - restyled only.
const STEPS = [
  {
    n: "1", title: "Basket selection",
    body: "Representative city-pairs are selected using DGCA domestic passenger-traffic data, covering all four aggregation regions (North, South, East, West India).",
  },
  {
    n: "2", title: "Route weighting",
    body: "Each route in the basket carries a weight derived from its share of DGCA passenger traffic. Weights are versioned (weight_set_version) and published alongside their source description.",
  },
  {
    n: "3", title: "Route price measure",
    body: "For each route and period, the platform computes four robust statistics — mean, median, trimmed mean (10%) and weighted median — and stores all four. The configured estimator (trimmed mean by default) becomes the route's price measure:",
    formula: "Route Index = (current route price measure / base-period price measure) × 100",
  },
  {
    n: "4", title: "Aggregation",
    formula: "Aggregate Index = Σ(route index × weight) / Σ(weight)",
    body: "A route-period with fewer than the minimum observation count is excluded and the remaining weights renormalised — the exclusion is recorded, never absorbed silently.",
  },
  {
    n: "5", title: "Quality filtering",
    body: "Only observations scoring at or above the quality threshold (60/100 by default, across eight weighted factors) enter index computation.",
  },
  {
    n: "6", title: "Validation",
    body: "The index is back-tested out-of-sample against publicly available DGCA monthly average fare data over at least 30 days, reporting MAE, RMSE, MAPE, correlation and directional accuracy.",
  },
];

export default function PublicMethodologyPage() {
  return (
    <div className="max-w-content mx-auto px-5 py-14">
      <Breadcrumbs items={[{ label: "Home", href: "/home" }, { label: "Methodology" }]} />
      <h1 className="b-display text-4xl lg:text-6xl mb-4">Show Your Work.</h1>
      <p className="text-base max-w-2xl mb-14 opacity-80 border-l-[var(--b-border)] border-[var(--b-signal)] pl-4">
        A judge, statistician or economist should be able to read this page and reproduce a
        published index value by hand.
      </p>

      <div className="max-w-3xl space-y-0">
        {STEPS.map((s) => (
          <section key={s.n} className="border-t-[var(--b-border)] border-[var(--b-ink)] py-7 flex gap-6">
            <span className="b-mono-tag text-3xl opacity-25 shrink-0 w-12">{s.n}</span>
            <div className="flex-1">
              <h2 className="font-extrabold text-lg uppercase tracking-tight mb-2">{s.title}</h2>
              {s.body && <p className="text-sm leading-relaxed opacity-80 mb-3">{s.body}</p>}
              {s.formula && (
                <code className="block border-[2px] border-[var(--b-ink)] bg-[var(--b-paper-alt)] p-3 text-xs mono">
                  {s.formula}
                </code>
              )}
            </div>
          </section>
        ))}
        <div className="border-t-[var(--b-border)] border-[var(--b-ink)]" />
      </div>

      <div className="flex gap-4 mt-12 flex-wrap">
        <Link href="/index-explorer/methodology" className="b-btn b-btn-outline text-xs">
          View live configuration <ArrowUpRight size={14} />
        </Link>
        <Link href="/backtesting" className="b-btn b-btn-outline text-xs">
          Backtesting Lab <ArrowUpRight size={14} />
        </Link>
      </div>
    </div>
  );
}
