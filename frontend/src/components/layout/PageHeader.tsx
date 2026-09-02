// Sized well below the marketing hero's 6xl/7xl (a page title, not a landing headline
// - every one of these 13 app pages needs room for its own content below), but pushed
// noticeably bigger/blacker than before to carry the same visual weight in miniature.
export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 mb-5 pb-4 border-b-[var(--border-hard-thick)] border-border-strong">
      <div>
        <h1 className="text-[34px] font-extrabold uppercase tracking-[-0.02em] leading-[0.95] text-primary">{title}</h1>
        {subtitle && <p className="text-sm text-muted mt-2">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
  );
}
