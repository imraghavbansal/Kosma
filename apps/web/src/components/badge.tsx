const VARIANTS = {
  success: "bg-success/10 text-success ring-success/20",
  danger: "bg-danger/10 text-danger ring-danger/20",
  warning: "bg-warning/10 text-warning ring-warning/20",
  accent: "bg-accent/10 text-accent ring-accent/20",
  neutral: "bg-surface-2 text-muted ring-border-strong",
};

export function Badge({
  children,
  variant = "neutral",
}: {
  children: React.ReactNode;
  variant?: keyof typeof VARIANTS;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${VARIANTS[variant]}`}
    >
      {children}
    </span>
  );
}
