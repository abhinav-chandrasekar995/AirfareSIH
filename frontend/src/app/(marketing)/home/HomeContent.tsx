"use client";
import Link from "next/link";
import { ArrowRight, ArrowUpRight, TrendingUp, AlertTriangle, CalendarClock, Calculator, LineChart, Plane } from "lucide-react";
import { useRevealOnScroll } from "@/lib/useRevealOnScroll";
import { useIndexSummary } from "@/lib/api/hooks";
import { num, pct } from "@/lib/format";

// All five hero features preserved verbatim from the original page - restyled only.
const HERO_FEATURES = [
  { icon: TrendingUp, num: "01", title: "India Airfare Price Index", desc: "A national, route-weighted index constructed from robust statistics, updated daily.", href: "/index-explorer" },
  { icon: AlertTriangle, num: "02", title: "Anomaly & Surge Intelligence", desc: "Expected-vs-observed baselines with model-based factor attribution.", href: "/anomalies" },
  { icon: CalendarClock, num: "03", title: "Lead-Time Intelligence", desc: "How booking timing — T+1 through T+45 — drives fare.", href: "/lead-time" },
  { icon: Calculator, num: "04", title: "CPI Augmentation Simulator", desc: "A scenario tool for how a high-frequency airfare signal could augment CPI analysis.", href: "/cpi-simulator" },
  { icon: LineChart, num: "05", title: "Backtesting & Forecasting", desc: "Validated against DGCA benchmarks; 14-day forecasts with intervals.", href: "/backtesting" },
];

const PHILOSOPHY = ["Collect", "Clean", "Measure", "Explain", "Validate", "Predict", "Augment"];

export default function HomeContent() {
  const revealRef = useRevealOnScroll<HTMLDivElement>();
  // Real, live-fetched index - never a hardcoded illustrative figure (build prompt
  // Sec.36: "do not hardcode impressive-looking numbers independently into components").
  // The same rule the app pages follow applies to the marketing hero too.
  const { data: summary, isLoading } = useIndexSummary();
  const headline = summary?.data.headline;

  return (
    <div ref={revealRef}>
      {/* Hero - primary CTA above the fold, raw asymmetric split */}
      <section className="b-grid-skew border-b-[var(--b-border-thick)] border-[var(--b-ink)]">
        <div className="px-5 md:px-10 py-16 lg:py-24 border-r-0 md:border-r-[var(--b-border)] border-[var(--b-ink)]">
          <span className="b-mono-tag inline-block border-[2px] border-[var(--b-ink)] px-2.5 py-1 mb-6">
            Statistical intelligence — not a booking site
          </span>
          <h1 className="b-display text-[13vw] sm:text-6xl lg:text-7xl max-w-2xl">
            India&apos;s Airfare, <span className="text-[var(--b-signal)]">Measured</span> Intelligently.
          </h1>
          <p className="text-base lg:text-lg mt-7 max-w-lg leading-relaxed opacity-85">
            We transform fragmented online airfare observations into a transparent,
            route-weighted Airfare Price Index — explaining abnormal price movements,
            validating against DGCA benchmarks, and demonstrating how high-frequency
            airfare data can augment official statistical analysis.
          </p>
          <div className="flex items-center gap-4 mt-9 flex-wrap">
            <Link href="/dashboard" className="b-btn">
              Explore the Dashboard <ArrowUpRight size={16} strokeWidth={2.5} />
            </Link>
            <Link href="/methodology" className="b-btn b-btn-outline">
              Understand the Methodology
            </Link>
          </div>
        </div>
        <div className="hidden md:flex items-center justify-center p-10 bg-[var(--b-ink)] text-[var(--b-paper)] relative overflow-hidden">
          <Plane size={220} strokeWidth={0.6} className="opacity-10 absolute -rotate-12" />
          <div className="relative z-10 text-center">
            <div className="b-mono-tag text-[var(--b-amber)] mb-2">India Airfare Index — Live</div>
            {isLoading ? (
              <div className="b-display text-6xl opacity-30 animate-pulse">···</div>
            ) : headline ? (
              <>
                <div className="b-display text-6xl">{num(headline.current_value, 1)}</div>
                <div className="b-mono-tag mt-2 text-[var(--b-signal)]">
                  {headline.change_pct !== null ? (
                    <>{headline.change_pct > 0 ? "▲" : headline.change_pct < 0 ? "▼" : "–"} {pct(headline.change_pct)} MoM</>
                  ) : (
                    "base period"
                  )}
                </div>
              </>
            ) : (
              <div className="b-display text-4xl opacity-50">No data yet</div>
            )}
          </div>
        </div>
      </section>

      {/* Product philosophy - infinite marquee */}
      <section className="b-marquee py-5">
        <div className="b-marquee-track">
          {[...PHILOSOPHY, ...PHILOSOPHY, ...PHILOSOPHY].map((step, i) => (
            <span key={i} className="b-mono-tag text-base px-8 flex items-center gap-8">
              {step} <ArrowRight size={16} />
            </span>
          ))}
        </div>
      </section>

      {/* Hero features - five raw blocks */}
      <section id="platform" className="max-w-content mx-auto px-5 py-16 lg:py-24">
        <div className="b-reveal mb-10 flex items-end justify-between flex-wrap gap-4">
          <h2 className="b-display text-3xl lg:text-4xl max-w-xl">Five modules that reinforce each other</h2>
          <span className="b-mono-tag opacity-60">One observation → every layer</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
          {HERO_FEATURES.map(({ icon: Icon, num, title, desc, href }, i) => (
            <Link
              key={title}
              href={href}
              data-reveal-delay={i * 90}
              className="b-reveal b-block p-5 flex flex-col bg-[var(--b-paper)]"
            >
              <div className="flex items-start justify-between mb-4">
                <Icon size={22} strokeWidth={2.25} />
                <span className="b-mono-tag opacity-40">{num}</span>
              </div>
              <h3 className="font-extrabold text-sm uppercase tracking-tight mb-2 leading-snug">{title}</h3>
              <p className="text-xs opacity-70 leading-relaxed">{desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Closing statement */}
      <section className="border-t-[var(--b-border-thick)] border-[var(--b-ink)] bg-[var(--b-ink)] text-[var(--b-paper)] py-16">
        <div className="b-reveal max-w-content mx-auto px-5 text-center">
          <p className="b-display text-2xl lg:text-4xl max-w-3xl mx-auto leading-tight">
            Not another flight-price tracker.
            <br />
            An end-to-end statistical intelligence platform.
          </p>
          <p className="text-sm opacity-70 mt-5 max-w-xl mx-auto">
            Built for policymakers, statistical organisations, regulators, economists and aviation analysts.
          </p>
          <Link href="/about" className="b-btn mt-8 inline-flex bg-[var(--b-signal)] border-[var(--b-paper)] shadow-[6px_6px_0_0_var(--b-paper)]">
            Read more about the platform <ArrowUpRight size={16} strokeWidth={2.5} />
          </Link>
        </div>
      </section>
    </div>
  );
}
