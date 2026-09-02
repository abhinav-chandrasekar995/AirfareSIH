import type { Metadata } from "next";
export const metadata: Metadata = {
  title: "Dashboard",
  description: "Executive overview of India's airfare market: national index, top movers, pressure map and computed insights.",
  alternates: { canonical: "/dashboard" },
};
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return children;
}
