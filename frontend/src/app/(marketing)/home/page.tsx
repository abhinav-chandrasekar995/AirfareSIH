import type { Metadata } from "next";
import HomeContent from "./HomeContent";

export const metadata: Metadata = {
  title: "Home",
  description:
    "India's airfare market, measured intelligently. A statistical platform transforming fragmented airfare observations into a transparent Airfare Price Index, anomaly intelligence, and CPI augmentation simulation.",
  alternates: { canonical: "/home" },
};

export default function HomePage() {
  return <HomeContent />;
}
