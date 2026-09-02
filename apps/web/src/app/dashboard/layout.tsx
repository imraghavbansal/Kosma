"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { UserMenu } from "@/components/user-menu";
import { ThemeToggle } from "@/components/theme-toggle";
import { SidebarStatus } from "@/components/sidebar-status";

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
    section: "WORKSPACE",
    items: [
      { label: "Projects", href: "/dashboard/projects" },
      { label: "Agents & Configs", href: "/dashboard/agents" },
      { label: "Settings", href: "/dashboard/settings" },
    ],
  },
];

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Propose a Change",
  "/dashboard/scorecard": "Prediction Scorecard",
  "/dashboard/traces": "Traces",
  "/dashboard/failure-clusters": "Failure Clusters",
  "/dashboard/regression-tests": "Regression Tests",
  "/dashboard/agents": "Agents & Configs",
  "/dashboard/settings": "Settings",
  "/dashboard/projects": "Projects",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // Close the mobile drawer on route change so it doesn't stay open after navigating.
  useEffect(() => {
    setMobileNavOpen(false);
  }, [pathname]);

  const pageTitle =
    PAGE_TITLES[pathname] ??
    (pathname.startsWith("/dashboard/traces/")
      ? "Trace Detail"
      : pathname.startsWith("/dashboard/changes/")
        ? "Change Detail"
        : pathname.startsWith("/dashboard/projects/")
          ? "Project Detail"
          : "Kosma");

  return (
    <div className="flex min-h-screen bg-background">
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
        <SidebarStatus />
        <p className="mt-3 px-2 text-[10px] text-muted">
          <a
            href="https://github.com/imraghavbansal/Kosma"
            target="_blank"
            rel="noreferrer"
            className="transition-colors duration-150 hover:text-foreground"
          >
            v0.1 · source
          </a>
        </p>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-border bg-surface/80 px-4 py-3 backdrop-blur-sm lg:px-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileNavOpen((v) => !v)}
              aria-label="Toggle navigation"
              className="flex h-8 w-8 items-center justify-center rounded-md text-foreground transition-colors duration-150 hover:bg-surface-2 lg:hidden"
            >
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                {mobileNavOpen ? <path d="M18 6L6 18M6 6l12 12" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
              </svg>
            </button>
            <h2 key={pageTitle} className="animate-fade-in font-mono text-sm text-foreground/90">
              {pageTitle}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <UserMenu />
          </div>
        </header>

        <main className="flex-1 overflow-x-auto">
          <div key={pathname} className="animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
