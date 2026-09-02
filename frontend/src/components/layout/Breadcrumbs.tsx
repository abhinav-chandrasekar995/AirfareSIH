import Link from "next/link";
import { ChevronRight } from "lucide-react";

export interface Crumb { label: string; href?: string; }

// Schema-friendly breadcrumbs with JSON-LD (build prompt Sec.25 + SEO Sec.28).
export function Breadcrumbs({ items }: { items: Crumb[] }) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((c, i) => ({
      "@type": "ListItem", position: i + 1, name: c.label,
      ...(c.href ? { item: c.href } : {}),
    })),
  };
  return (
    <nav aria-label="Breadcrumb" className="mb-3">
      <ol className="flex items-center gap-1.5 text-xs text-muted flex-wrap">
        {items.map((c, i) => (
          <li key={i} className="flex items-center gap-1.5">
            {c.href ? (
              <Link href={c.href} className="hover:text-accent">{c.label}</Link>
            ) : (
              <span className="text-secondary font-medium" aria-current="page">{c.label}</span>
            )}
            {i < items.length - 1 && <ChevronRight size={12} aria-hidden />}
          </li>
        ))}
      </ol>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
    </nav>
  );
}
