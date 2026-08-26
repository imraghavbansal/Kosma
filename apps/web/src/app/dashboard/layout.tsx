import Link from "next/link";
import { LogoutButton } from "./logout-button";

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
  return (
    <div className="flex min-h-screen bg-background">
      <aside className="flex w-60 shrink-0 flex-col border-r border-border px-4 py-6">
        <div className="mb-8 px-2">
          <span className="font-mono text-sm font-semibold tracking-tight text-foreground">
            TRACEOS
          </span>
        </div>
        <nav className="flex-1 space-y-6">
          {NAV.map((group) => (
            <div key={group.section}>
              <p className="mb-2 px-2 text-[10px] font-medium tracking-wider text-muted">
                {group.section}
              </p>
              <ul className="space-y-0.5">
                {group.items.map((item) => (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className="block rounded-md px-2 py-1.5 text-sm text-foreground/80 transition-colors hover:bg-surface hover:text-foreground"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
        <LogoutButton />
      </aside>
      <main className="flex-1 overflow-x-auto">{children}</main>
    </div>
  );
}
