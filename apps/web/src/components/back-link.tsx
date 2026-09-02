import Link from "next/link";

export function BackLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="group mb-4 inline-flex items-center gap-1.5 text-xs text-muted transition-colors duration-150 hover:text-foreground"
    >
      <svg
        viewBox="0 0 16 16"
        className="h-3 w-3 transition-transform duration-150 ease-premium group-hover:-translate-x-0.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M10 12L6 8l4-4" />
      </svg>
      {label}
    </Link>
  );
}
