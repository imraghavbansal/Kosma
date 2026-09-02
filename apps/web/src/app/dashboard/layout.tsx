"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { LogoutButton } from "./logout-button";
import { UserBadge } from "@/components/user-badge";
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
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // Close the mobile drawer on route change so it doesn't stay open after navigating.
  useEffect(() => {
    setMobileNavOpen(false);
  }, [pathname]);

  return (
    <div className="flex min-h-screen bg-background">
      {/* Mobile top bar - hidden on lg+ where the sidebar is always visible */}
      <div className="fixed inset-x-0 top-0 z-30 flex items-center justify-between border-b border-border bg-surface px-4 py-3 lg:hidden">
        <span className="font-mono text-sm font-semibold tracking-tight text-foreground">KOSMA</span>
        <button
          onClick={() => setMobileNavOpen((v) => !v)}
          aria-label="Toggle navigation"
          className="flex h-8 w-8 items-center justify-center rounded-md text-foreground transition-colors duration-150 hover:bg-surface-2"
        >
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            {mobileNavOpen ? <path d="M18 6L6 18M6 6l12 12" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
          </svg>
        </button>
      </div>

      {/* Backdrop for the mobile drawer */}
      {mobileNavOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 transition-opacity duration-200 lg:hidden"
          onClick={() => setMobileNavOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 shrink-0 -translate-x-full flex-col border-r border-border bg-background px-4 py-6 transition-transform duration-300 ease-premium lg:static lg:w-60 lg:translate-x-0 ${
          mobileNavOpen ? "translate-x-0" : ""
        }`}
      >
        <div className="mb-8 flex items-center justify-between px-2">
          <span className="font-mono text-sm font-semibold tracking-tight text-foreground">
            KOSMA
          </span>
          <ThemeToggle />
        </div>
        <nav className="flex-1 space-y-6 overflow-y-auto">
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
        <UserBadge />
        <LogoutButton />
      </aside>

      <main className="flex-1 overflow-x-auto pt-14 lg:pt-0">
        <div key={pathname} className="animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
