"use client";
import { Moon, Sun, KeyRound } from "lucide-react";
import Link from "next/link";
import { useUiStore } from "@/lib/store/uiStore";
import { DataModeBadge } from "./DataModeBadge";
import { useDashboard } from "@/lib/api/hooks";
import { relativeTime } from "@/lib/format";

export function TopBar() {
  const { theme, toggleTheme } = useUiStore();
  const { data } = useDashboard();
  const meta = data?.meta;

  return (
    <header className="h-14 shrink-0 border-b-[var(--border-hard-thick)] border-border-strong bg-panel flex items-center justify-between px-4 gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <h1 className="text-sm font-extrabold uppercase tracking-tight text-primary hidden sm:block">India Airfare Intelligence</h1>
        {meta && (
          <span className="eyebrow hidden md:inline">
            Updated {relativeTime(meta.generated_at)}
          </span>
        )}
      </div>
      <div className="flex items-center gap-2">
        {meta && <DataModeBadge mode={meta.data_mode} label={meta.data_mode_label} description={meta.data_mode_description} />}
        <Link href="/api-portal/keys" className="p-2 border-[var(--border-hard)] border-transparent text-muted hover:text-primary hover:border-border-strong" aria-label="API keys" title="API keys">
          <KeyRound size={17} strokeWidth={2.25} />
        </Link>
        <button onClick={toggleTheme} className="p-2 border-[var(--border-hard)] border-transparent text-muted hover:text-primary hover:border-border-strong" aria-label="Toggle theme">
          {theme === "dark" ? <Sun size={17} strokeWidth={2.25} /> : <Moon size={17} strokeWidth={2.25} />}
        </button>
      </div>
    </header>
  );
}
