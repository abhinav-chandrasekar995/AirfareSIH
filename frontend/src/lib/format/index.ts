// Formatting helpers. Indian digit grouping in the UI; INR with the rupee glyph.

export function inr(value: number | null | undefined, decimals = 0): string {
  if (value === null || value === undefined) return "—";
  return "\u20B9" + value.toLocaleString("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function num(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function pct(value: number | null | undefined, decimals = 1, signed = true): string {
  if (value === null || value === undefined) return "—";
  const sign = signed && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(decimals)}%`;
}

export function compactNum(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (value >= 1e7) return (value / 1e7).toFixed(1) + "Cr";
  if (value >= 1e5) return (value / 1e5).toFixed(1) + "L";
  if (value >= 1e3) return (value / 1e3).toFixed(1) + "K";
  return String(value);
}

export function istDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
  });
}

export function istDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
  }) + " IST";
}

export function relativeTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const hours = Math.floor(diff / 3.6e6);
  if (hours < 1) return "just now";
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

// Direction convention: a rising fare is the adverse direction in a price index.
export function priceDirectionClass(changePct: number | null | undefined): string {
  if (changePct === null || changePct === undefined || Math.abs(changePct) < 0.5) return "text-price-flat";
  return changePct > 0 ? "text-price-up" : "text-price-down";
}
