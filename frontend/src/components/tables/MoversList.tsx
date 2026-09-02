import Link from "next/link";
import { DeltaChip } from "@/components/badges/DeltaChip";
import { inr } from "@/lib/format";
import type { Mover } from "@/types/api";
import { EmptyState } from "@/components/panels/EmptyState";

export function MoversList({ movers }: { movers: Mover[] }) {
  if (movers.length === 0) return <EmptyState title="No movers yet" message="Index history is too short to compute a 7-day change." />;
  return (
    <ul className="divide-y divide-border-subtle">
      {movers.map((m) => (
        <li key={m.route_code}>
          <Link href={`/routes/${m.route_code}`} className="flex items-center justify-between py-1.5 hover:bg-panel-alt/50 px-1 -mx-1 rounded-sm">
            <div className="min-w-0">
              <div className="text-xs font-medium text-primary mono">{m.route_code}</div>
              <div className="text-[11px] text-muted truncate">{m.origin_city} → {m.destination_city}</div>
            </div>
            <div className="text-right shrink-0">
              <div className="text-xs numeric text-secondary">{inr(m.current_fare)}</div>
              <DeltaChip value={m.change_pct} basis="7d" className="mt-0.5" />
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
