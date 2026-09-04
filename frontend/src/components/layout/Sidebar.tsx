"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, TrendingUp, Plane, AlertTriangle, CalendarClock, Calculator,
  LineChart, Database, RadioTower, Plug, FileText, Settings, ChevronLeft, Landmark,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/lib/store/uiStore";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/index-explorer", label: "Airfare Index", icon: TrendingUp },
  { href: "/routes", label: "Routes", icon: Plane },
  { href: "/lead-time", label: "Lead-Time", icon: CalendarClock },
  { href: "/anomalies", label: "Anomalies", icon: AlertTriangle },
  { href: "/forecast", label: "Forecast", icon: LineChart },
  { href: "/backtesting", label: "Backtesting", icon: LineChart },
  { href: "/cpi-simulator", label: "CPI Simulator", icon: Calculator },
  { href: "/rbi-policy", label: "RBI Policy", icon: Landmark },
  { href: "/data-explorer", label: "Data Explorer", icon: Database },
  { href: "/collection", label: "Collection", icon: RadioTower },
  { href: "/api-portal", label: "API Portal", icon: Plug },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useUiStore();

  return (
    <aside
      className={cn(
        "shrink-0 border-r-[var(--border-hard-thick)] border-border-strong bg-panel flex flex-col transition-all duration-200",
        sidebarCollapsed ? "w-16" : "w-56",
      )}
    >
      <div className="h-14 flex items-center gap-2.5 px-4 border-b-[var(--border-hard)] border-border-strong">
        <div className="h-8 w-8 border-[var(--border-hard)] border-border-strong bg-interactive flex items-center justify-center shrink-0">
          <Plane size={16} className="text-white" strokeWidth={2.5} />
        </div>
        {!sidebarCollapsed && (
          <div className="min-w-0">
            <div className="text-[12px] font-extrabold uppercase tracking-tight text-primary leading-tight truncate">Airfare Intel</div>
            <div className="text-[9.5px] font-mono text-muted leading-tight uppercase tracking-wide">India · Price Index</div>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto py-2" aria-label="Application">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-2.5 px-4 py-2 text-[12.5px] font-semibold uppercase tracking-tight transition-colors relative",
                active
                  ? "text-inverse bg-interactive"
                  : "text-secondary hover:text-primary hover:bg-panel-alt",
              )}
            >
              <Icon size={16} strokeWidth={2.25} className="shrink-0" />
              {!sidebarCollapsed && <span className="truncate">{label}</span>}
            </Link>
          );
        })}
      </nav>

      <button
        onClick={toggleSidebar}
        className="h-10 flex items-center justify-center gap-1.5 border-t-[var(--border-hard)] border-border-strong text-[11px] font-mono uppercase tracking-wide text-muted hover:text-primary hover:bg-panel-alt"
        aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        <ChevronLeft size={15} strokeWidth={2.5} className={cn("transition-transform", sidebarCollapsed && "rotate-180")} />
        {!sidebarCollapsed && <span>Collapse</span>}
      </button>
    </aside>
  );
}
