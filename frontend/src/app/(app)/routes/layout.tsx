import type { Metadata } from "next";
export const metadata: Metadata = {
  title: "Route Intelligence",
  description: "Every tracked India domestic city-pair with current fare, route index, and volatility score.",
  alternates: { canonical: "/routes" },
};
export default function RoutesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
