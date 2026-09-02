import type { Metadata } from "next";
import { Providers } from "@/lib/providers";
import "./globals.css";

const SITE_URL = "https://airfare-intelligence.example.org";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "India Airfare Intelligence — Real-Time Airfare Price Index",
    template: "%s — India Airfare Intelligence",
  },
  description:
    "A statistical intelligence platform measuring India's domestic airfare market: a route-weighted Airfare Price Index, anomaly detection, lead-time analysis, DGCA-validated backtesting, forecasting, and a CPI augmentation simulator.",
  applicationName: "India Airfare Intelligence",
  keywords: [
    "airfare price index", "India airfare", "DGCA benchmark", "CPI augmentation",
    "airfare statistics", "domestic airfare India", "fare anomaly detection",
  ],
  openGraph: {
    type: "website",
    siteName: "India Airfare Intelligence",
    title: "India Airfare Intelligence — Real-Time Airfare Price Index",
    description: "High-frequency statistical intelligence for India's domestic airfare market.",
    url: SITE_URL,
  },
  twitter: {
    card: "summary_large_image",
    title: "India Airfare Intelligence",
    description: "High-frequency statistical intelligence for India's domestic airfare market.",
  },
  robots: { index: true, follow: true },
};

const ORG_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "India Airfare Intelligence",
  url: SITE_URL,
  description: "Statistical intelligence platform for India's domestic airfare market.",
};

const WEBSITE_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "India Airfare Intelligence",
  url: SITE_URL,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-IN" data-theme="dark" suppressHydrationWarning>
      <body>
        <a href="#main" className="skip-link">Skip to main content</a>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ORG_JSON_LD) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(WEBSITE_JSON_LD) }} />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
