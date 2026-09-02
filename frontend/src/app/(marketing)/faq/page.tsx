import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";

export const metadata: Metadata = {
  title: "FAQ",
  description: "Frequently asked questions about the India Airfare Price Index, data collection, quality handling, the CPI simulator, and source resilience.",
  alternates: { canonical: "/faq" },
};

const FAQS = [
  {
    q: "What is the India Airfare Price Index?",
    a: "It is a route-weighted statistical index constructed from quality-filtered airfare observations collected across airlines and OTAs. Representative city-pairs are selected using DGCA passenger-traffic data, each route's price is measured with a robust estimator (trimmed mean by default), and route indices are aggregated into national, regional and airline-level indices using versioned weights. Every published value references a methodology_version so it can be reproduced.",
    link: { href: "/index-explorer/methodology", label: "View the methodology" },
  },
  {
    q: "How does the platform collect airfare data?",
    a: "Each source (airline or OTA) has an isolated adapter implementing a common interface (fetch + parse). A shared guard chain enforces robots.txt awareness, per-source rate limits, response caching and circuit breaking before any request is made, and a challenge detector stops collection immediately if a source returns a CAPTCHA or access-control page — the platform never attempts to bypass one. Collection is scheduled, not triggered by user requests.",
    link: { href: "/collection", label: "View collection engine status" },
  },
  {
    q: "How are unreliable or bad fare observations handled?",
    a: "Every observation passes a fixed seven-step pipeline: schema validation, normalisation, deduplication, controlled missing-value handling, outlier flagging, fare decomposition, and quality scoring (0–100 across eight factors). Raw observations are immutable and retained separately from the cleaned record. Only observations scoring at or above the quality threshold (60 by default) enter index computation; the threshold is recorded with every published value.",
    link: { href: "/data-explorer", label: "Inspect raw vs cleaned observations" },
  },
  {
    q: "Is the CPI Augmentation Simulator an official CPI calculation?",
    a: "No. It is explicitly a simulation for analytical demonstration, not an official CPI revision or NSO methodology. The simulator combines a base CPI figure with our airfare index at a user-adjustable weight to illustrate how a high-frequency airfare signal could theoretically augment CPI-style analysis. This disclaimer is shown on-screen at all times and included in the module's API responses — it cannot be dismissed.",
    link: { href: "/cpi-simulator", label: "Open the CPI simulator" },
  },
  {
    q: "What happens if an airline or OTA data source becomes unavailable?",
    a: "The pipeline degrades gracefully: Source Down → Fallback Source → Data-Quality Flag → Index Continues. A circuit breaker stops repeated requests to a failing source; the orchestrator retries with a configured fallback source; the substitution is recorded as a data-quality flag rather than hidden; and the index still publishes using the routes and sources that remain available.",
    link: { href: "/collection", label: "View source health" },
  },
];

const FAQ_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: FAQS.map((f) => ({
    "@type": "Question",
    name: f.q,
    acceptedAnswer: { "@type": "Answer", text: f.a },
  })),
};

export default function FaqPage() {
  return (
    <div className="max-w-content mx-auto px-5 py-14">
      <Breadcrumbs items={[{ label: "Home", href: "/home" }, { label: "FAQ" }]} />
      <h1 className="b-display text-4xl lg:text-6xl mb-10">
        Questions,<br />Answered Directly.
      </h1>

      <div className="max-w-3xl">
        {FAQS.map((f, i) => (
          <article key={f.q} className="b-block p-6 mb-6 bg-[var(--b-paper)]">
            <div className="flex items-start gap-4">
              <span className="b-mono-tag text-2xl opacity-25 shrink-0 leading-none">{String(i + 1).padStart(2, "0")}</span>
              <div>
                <h2 className="font-extrabold text-base uppercase tracking-tight mb-2">{f.q}</h2>
                <p className="text-sm leading-relaxed opacity-80">{f.a}</p>
                {f.link && (
                  <Link href={f.link.href} className="inline-flex items-center gap-1 mt-4 b-mono-tag text-[var(--b-signal)] hover:underline">
                    {f.link.label} <ArrowUpRight size={13} strokeWidth={2.5} />
                  </Link>
                )}
              </div>
            </div>
          </article>
        ))}
      </div>

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(FAQ_JSON_LD) }} />
    </div>
  );
}
