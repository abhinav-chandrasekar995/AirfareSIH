import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";

export const metadata: Metadata = {
  title: "About",
  description:
    "India Airfare Intelligence is a high-frequency statistical intelligence system for India's domestic aviation market, built for policymakers, statistical organisations, regulators, economists and researchers.",
  alternates: { canonical: "/about" },
};

// Content preserved verbatim from the original page - restyled only.
const PRINCIPLES = [
  { title: "Statistical First", desc: "The index methodology matters more than visual effects." },
  { title: "Consumer-Centric", desc: "We measure the final fare a traveller actually faces, not just an advertised base fare." },
  { title: "Explainable", desc: "Every significant price movement carries an interpretable, model-based explanation." },
  { title: "Reproducible", desc: "Any index value can be recomputed from stored observations and its methodology version." },
  { title: "Resilient", desc: "The system keeps functioning when any single source becomes unavailable." },
  { title: "Policy-Oriented", desc: "The output has relevance beyond flight-price comparison — for CPI analysis and market oversight." },
];

const AUDIENCE = ["Policymakers", "Statistical organisations", "Regulators", "Economists", "Researchers", "Aviation analysts"];

export default function AboutPage() {
  return (
    <div className="max-w-content mx-auto px-5 py-14">
      <Breadcrumbs items={[{ label: "Home", href: "/home" }, { label: "About" }]} />

      <h1 className="b-display text-4xl lg:text-6xl mb-3">About the Platform</h1>
      <p className="text-base max-w-2xl mb-14 opacity-80 border-l-[var(--b-border)] border-[var(--b-signal)] pl-4">
        A high-frequency airfare statistical intelligence system for India&apos;s domestic aviation market.
      </p>

      <section className="mb-14 b-grid-skew gap-8 !grid-cols-1 md:!grid-cols-[220px_1fr]">
        <h2 className="b-mono-tag text-base">01 / What is it?</h2>
        <p className="text-sm leading-relaxed max-w-3xl">
          India Airfare Intelligence collects airfare observations from airline websites and Online
          Travel Aggregators, cleans and quality-scores them, and constructs a transparent,
          route-weighted <strong>Airfare Price Index</strong>. It is not a flight-booking website —
          it is a measurement instrument, closer in spirit to a financial data terminal than a
          travel app.
        </p>
      </section>

      <section className="mb-14 b-grid-skew gap-8 !grid-cols-1 md:!grid-cols-[220px_1fr]">
        <h2 className="b-mono-tag text-base">02 / The Problem</h2>
        <p className="text-sm leading-relaxed max-w-3xl">
          India&apos;s domestic airfare market is highly dynamic: prices vary by route, airline,
          booking lead time, demand, seat availability and seasonality. Traditional price
          collection is infrequent and fragmented across dozens of digital sources, making it
          difficult to answer a simple question at any given moment: what is actually happening to
          airfare prices in India?
        </p>
      </section>

      <section className="mb-14 b-grid-skew gap-8 !grid-cols-1 md:!grid-cols-[220px_1fr]">
        <h2 className="b-mono-tag text-base">03 / The Solution</h2>
        <div>
          <div className="flex flex-wrap items-center gap-2">
            {["Collect", "Clean", "Measure", "Explain", "Validate", "Predict", "Augment"].map((step) => (
              <span key={step} className="b-mono-tag border-[2px] border-[var(--b-ink)] px-2.5 py-1">{step}</span>
            ))}
          </div>
          <p className="text-sm leading-relaxed max-w-3xl mt-4">
            Each stage of this pipeline is a real, auditable system component — not a marketing
            diagram. Raw observations are immutable; cleaned observations carry a quality score;
            published index values reference a methodology version; anomalies carry model-based
            attribution; forecasts always carry a prediction interval; and the CPI module is clearly
            labelled as a simulation.
          </p>
        </div>
      </section>

      <section className="mb-14 b-grid-skew gap-8 !grid-cols-1 md:!grid-cols-[220px_1fr]">
        <h2 className="b-mono-tag text-base">04 / Who It&apos;s For</h2>
        <div className="flex flex-wrap gap-2">
          {AUDIENCE.map((a) => (
            <span key={a} className="text-xs font-bold uppercase border-[2px] border-[var(--b-ink)] px-3 py-1.5">{a}</span>
          ))}
        </div>
      </section>

      <section className="mb-14">
        <h2 className="b-display text-2xl lg:text-3xl mb-6">Principles</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {PRINCIPLES.map((p, i) => (
            <div key={p.title} className="b-block p-5">
              <span className="b-mono-tag opacity-40">{String(i + 1).padStart(2, "0")}</span>
              <h3 className="font-extrabold text-sm uppercase tracking-tight mt-2 mb-1.5">{p.title}</h3>
              <p className="text-xs opacity-70 leading-relaxed">{p.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="flex gap-4 flex-wrap pt-8 border-t-[var(--b-border)] border-[var(--b-ink)]">
        <Link href="/methodology" className="b-btn b-btn-outline text-xs">Methodology <ArrowUpRight size={14} /></Link>
        <Link href="/dashboard" className="b-btn b-btn-outline text-xs">Dashboard <ArrowUpRight size={14} /></Link>
        <Link href="/api-portal" className="b-btn b-btn-outline text-xs">API Portal <ArrowUpRight size={14} /></Link>
      </section>
    </div>
  );
}
