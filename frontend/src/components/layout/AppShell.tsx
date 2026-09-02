"use client";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { useRevealOnScroll } from "@/lib/useRevealOnScroll";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  // Scroll-reveal for every PanelShell/KpiCard on the page, matching the marketing
  // site's entrance motion. `key={pathname}` remounts the wrapper on each client-side
  // navigation. The hook itself is fail-safe: content the observer never reaches (e.g.
  // panels still behind a loading skeleton at the moment this effect runs) simply stays
  // visible with no animation, rather than staying hidden - see useRevealOnScroll.ts.
  const revealRef = useRevealOnScroll<HTMLDivElement>(".reveal");

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main id="main" className="flex-1 overflow-y-auto">
          <div key={pathname} ref={revealRef} className="max-w-content mx-auto p-4 lg:p-5">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
