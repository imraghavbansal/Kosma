"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogoutButton } from "./logout-button";
import { ThemeToggle } from "@/components/theme-toggle";

const NAV = [
  {
    section: "CHANGE INTELLIGENCE",
    items: [
      { label: "Propose a Change", href: "/dashboard" },
      { label: "Prediction Scorecard", href: "/dashboard/scorecard" },
    ],
  },
  {
    section: "EVIDENCE",
    items: [
      { label: "Traces", href: "/dashboard/traces" },
      { label: "Failure Clusters", href: "/dashboard/failure-clusters" },
      { label: "Regression Tests", href: "/dashboard/regression-tests" },
    ],
  },
  {
    section: "PROJECT",
    items: [
      { label: "Agents & Configs", href: "/dashboard/agents" },
      { label: "Settings", href: "/dashboard/settings" },
    ],
  },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="flex w-60 shrink-0 flex-col border-r border-border px-4 py-6">
        <div className="mb-8 flex items-center justify-between px-2">
          <span className="font-mono text-sm font-semibold tracking-tight text-foreground">
            KOSMA
          </span>
          <ThemeToggle />
        </div>
        <nav className="flex-1 space-y-6">
          {NAV.map((group) => (
            <div key={group.section}>
              <p className="mb-2 px-2 text-[10px] font-medium tracking-wider text-muted">
                {group.section}
              </p>
              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive =
                    item.href === "/dashboard" ? pathname === item.href : pathname.startsWith(item.href);
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className={`group relative block rounded-md px-2 py-1.5 text-sm transition-all duration-200 ease-premium ${
                          isActive
                            ? "bg-surface-2 text-foreground"
                            : "text-foreground/70 hover:bg-surface-2/60 hover:text-foreground"
                        }`}
                      >
                        {isActive && (
                          <span className="absolute -left-4 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-accent" />
                        )}
                        {item.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
        <LogoutButton />
      </aside>
      <main className="flex-1 overflow-x-auto">
        <div key={pathname} className="animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
