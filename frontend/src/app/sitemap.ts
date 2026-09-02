import type { MetadataRoute } from "next";

const BASE = "https://airfare-intelligence.example.org";

// Only crawlable public pages (build prompt Sec.28). App pages behind the sidebar are
// data-driven and excluded via robots.ts rather than listed here.
export default function sitemap(): MetadataRoute.Sitemap {
  const routes = ["/home", "/about", "/faq", "/methodology", "/api-portal"];
  return routes.map((path) => ({
    url: `${BASE}${path}`,
    lastModified: new Date(),
    changeFrequency: "weekly",
    priority: path === "/home" ? 1 : 0.7,
  }));
}
