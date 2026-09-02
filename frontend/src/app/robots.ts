import type { MetadataRoute } from "next";

// Protected application pages (dashboard, routes, anomalies, data explorer, admin
// surfaces) are not crawled - they render live analytical data, not indexable content,
// and the API requires authentication above the PUBLIC role (build prompt Sec.28).
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/home", "/about", "/faq", "/methodology", "/api-portal"],
        disallow: [
          "/dashboard", "/index-explorer", "/routes", "/lead-time", "/anomalies",
          "/forecast", "/backtesting", "/cpi-simulator", "/data-explorer",
          "/collection", "/reports", "/settings", "/api-portal/keys", "/backend",
        ],
      },
    ],
    sitemap: "https://airfare-intelligence.example.org/sitemap.xml",
  };
}
