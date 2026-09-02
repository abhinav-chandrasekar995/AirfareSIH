// Typed API client. Talks to the backend through the Next.js rewrite proxy (/backend/*)
// so the browser sees a single origin. Every backend response is the standard envelope.

export interface Meta {
  count: number;
  page: number;
  page_size: number;
  total: number | null;
  granularity: string | null;
  data_mode: string;
  data_mode_label: string;
  data_mode_description: string | null;
  is_live: boolean;
  generated_at: string;
  sources_included: string[];
  quality_threshold: number;
  estimator: string | null;
  notes: string | null;
}

export interface Envelope<T> {
  data: T;
  meta: Meta;
  methodology_version: string;
  disclaimer: string | null;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

const BASE = "/backend/api/v1";

function getApiKey(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("iai_api_key");
}

export async function apiGet<T>(
  path: string,
  params?: Record<string, string | number | boolean | undefined | null>,
): Promise<Envelope<T>> {
  const url = new URL(`${BASE}${path}`, typeof window !== "undefined" ? window.location.origin : "http://localhost:3000");
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }

  const headers: Record<string, string> = { Accept: "application/json" };
  const key = getApiKey();
  if (key) headers["X-API-Key"] = key;

  const response = await fetch(url.toString().replace(url.origin, ""), { headers, cache: "no-store" });

  if (!response.ok) {
    let code = "error";
    let message = `request failed (${response.status})`;
    try {
      const body = await response.json();
      code = body?.error?.code ?? code;
      message = body?.error?.message ?? message;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(response.status, code, message);
  }

  return (await response.json()) as Envelope<T>;
}

// Absolute backend URL, for links to OpenAPI docs etc.
export function backendUrl(path: string): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  return `${base}${path}`;
}
