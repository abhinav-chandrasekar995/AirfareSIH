import Link from "next/link";
import { Plane, ArrowUpRight } from "lucide-react";

// Every link from the original layout is preserved verbatim - this is a restyle, not a
// re-scope. See IMPLEMENTATION_LOG.md for the brutalism-on-marketing-only decision.
const NAV = [
  { href: "/home", label: "Home" },
  { href: "/home#platform", label: "Platform" },
  { href: "/methodology", label: "Methodology" },
  { href: "/about", label: "About" },
  { href: "/faq", label: "FAQ" },
  { href: "/api-portal", label: "API Portal" },
];

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="brutal min-h-screen flex flex-col">
      <header className="border-b-[var(--b-border-thick)] border-[var(--b-ink)] bg-[var(--b-paper)] sticky top-0 z-40">
        <nav className="max-w-content mx-auto flex items-center justify-between px-5 py-4 gap-4" aria-label="Primary">
          <Link href="/home" className="flex items-center gap-2.5 shrink-0 group">
            <span className="h-9 w-9 border-[3px] border-[var(--b-ink)] bg-[var(--b-signal)] flex items-center justify-center group-hover:-translate-y-0.5 group-hover:-translate-x-0.5 transition-transform">
              <Plane size={18} className="text-white" strokeWidth={2.5} />
            </span>
            <span className="b-display text-sm md:text-base leading-none">
              India<br className="hidden sm:block" /> Airfare Intel
            </span>
          </Link>
          <div className="hidden lg:flex items-center gap-6">
            {NAV.map((n) => (
              <Link key={n.href} href={n.href} className="b-mono-tag text-[var(--b-ink)] hover:text-[var(--b-signal)] transition-colors">
                {n.label}
              </Link>
            ))}
          </div>
          <Link href="/dashboard" className="b-btn text-xs shrink-0">
            Open Dashboard <ArrowUpRight size={14} strokeWidth={2.5} />
          </Link>
        </nav>
      </header>

      <main id="main" className="flex-1">{children}</main>

      <footer className="border-t-[var(--b-border-thick)] border-[var(--b-ink)] bg-[var(--b-ink)] text-[var(--b-paper)] py-12">
        <div className="max-w-content mx-auto px-5 grid grid-cols-2 md:grid-cols-4 gap-8 text-xs">
          <div>
            <div className="b-mono-tag text-[var(--b-amber)] mb-3">Platform</div>
            <Link href="/dashboard" className="block py-1 hover:text-[var(--b-signal)]">Dashboard</Link>
            <Link href="/index-explorer" className="block py-1 hover:text-[var(--b-signal)]">Airfare Index</Link>
            <Link href="/cpi-simulator" className="block py-1 hover:text-[var(--b-signal)]">CPI Simulator</Link>
          </div>
          <div>
            <div className="b-mono-tag text-[var(--b-amber)] mb-3">Learn</div>
            <Link href="/methodology" className="block py-1 hover:text-[var(--b-signal)]">Methodology</Link>
            <Link href="/about" className="block py-1 hover:text-[var(--b-signal)]">About</Link>
            <Link href="/faq" className="block py-1 hover:text-[var(--b-signal)]">FAQ</Link>
          </div>
          <div>
            <div className="b-mono-tag text-[var(--b-amber)] mb-3">Developers</div>
            <Link href="/api-portal" className="block py-1 hover:text-[var(--b-signal)]">API Portal</Link>
            <Link href="/api-portal/keys" className="block py-1 hover:text-[var(--b-signal)]">API Keys</Link>
          </div>
          <div>
            <div className="b-mono-tag text-[var(--b-amber)] mb-3">Platform note</div>
            <p className="opacity-80 leading-relaxed">A statistical intelligence system for India&apos;s domestic airfare market — not a booking service.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
