import Link from "next/link";
import { Plane, LayoutDashboard, Home, TrendingUp, AlertTriangle, Calculator } from "lucide-react";

// Custom 404 matching the platform's visual identity (build prompt Sec.26).
// Not a generic browser error page. Brutalist treatment applies here regardless of
// which route the user came from - this is a one-off interstitial, not a workflow
// page, so a bold departure from either the marketing or app chrome does no harm and
// a stark "404" is a natural fit for the style.
export default function NotFound() {
  return (
    <div className="brutal min-h-screen flex items-center justify-center px-5 py-12 relative overflow-hidden">
      <Plane size={480} strokeWidth={0.5} className="opacity-[0.04] absolute -rotate-45 pointer-events-none" />
      <div className="text-center max-w-lg relative z-10">
        <div className="h-14 w-14 border-[3px] border-[var(--b-ink)] bg-[var(--b-signal)] flex items-center justify-center mx-auto mb-7">
          <Plane size={26} className="text-white" strokeWidth={2.5} />
        </div>
        <div className="b-display text-[8rem] leading-none mb-2 text-[var(--b-signal)]">404</div>
        <h1 className="font-extrabold text-xl uppercase tracking-tight mb-3">This intelligence page could not be found.</h1>
        <p className="text-sm mb-9 leading-relaxed opacity-75 max-w-sm mx-auto">
          The route, report or analytical view you requested does not exist — or the observations
          behind it have not been computed yet. It has not been deleted from the index.
        </p>
        <div className="flex items-center justify-center gap-3 mb-9 flex-wrap">
          <Link href="/dashboard" className="b-btn text-sm">
            <LayoutDashboard size={16} /> Go to Dashboard
          </Link>
          <Link href="/home" className="b-btn b-btn-outline text-sm">
            <Home size={16} /> Home
          </Link>
        </div>
        <div className="flex items-center justify-center gap-5 text-xs border-t-[2px] border-[var(--b-ink)] pt-6">
          <Link href="/index-explorer" className="b-mono-tag flex items-center gap-1.5 opacity-70 hover:opacity-100 hover:text-[var(--b-signal)]"><TrendingUp size={13} /> Airfare Index</Link>
          <Link href="/anomalies" className="b-mono-tag flex items-center gap-1.5 opacity-70 hover:opacity-100 hover:text-[var(--b-signal)]"><AlertTriangle size={13} /> Anomalies</Link>
          <Link href="/cpi-simulator" className="b-mono-tag flex items-center gap-1.5 opacity-70 hover:opacity-100 hover:text-[var(--b-signal)]"><Calculator size={13} /> CPI Simulator</Link>
        </div>
      </div>
    </div>
  );
}
