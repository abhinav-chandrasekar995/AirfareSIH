import type { Metadata } from "next";
export const metadata: Metadata = {
  title: "API Portal",
  description: "Versioned REST API for the India Airfare Price Index, anomalies, forecasts and CPI simulation, with authentication and rate limiting.",
  alternates: { canonical: "/api-portal" },
};
export default function ApiPortalLayout({ children }: { children: React.ReactNode }) {
  return children;
}
