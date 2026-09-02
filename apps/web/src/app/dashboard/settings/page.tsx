import { redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { Badge } from "@/components/badge";
import { LogoutButton } from "../logout-button";
import { ThemeToggle } from "@/components/theme-toggle";

export default async function SettingsPage() {
  const meRes = await serverApiFetch("/v1/auth/me");
  if (meRes.status === 401) redirect("/login");
  const me = meRes.ok ? await meRes.json() : { user: null };

  return (
    <div className="p-8">
      <h1 className="font-mono text-xl text-foreground">Settings</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Your session, this deployment&apos;s configuration, and where to read more.
      </p>

      <div className="mt-6 max-w-2xl space-y-6">
        <div className="animate-fade-in flex items-center gap-4 rounded-lg border border-border bg-surface p-5">
          {me.user?.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={me.user.avatar_url}
              alt={me.user.github_username}
              className="h-14 w-14 rounded-full ring-1 ring-border"
            />
          ) : (
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent font-mono text-lg font-bold text-accent-foreground">
              K
            </div>
          )}
          <div className="flex-1">
            <p className="text-base font-medium text-foreground">
              {me.user ? (me.user.display_name ?? me.user.github_username) : "Project owner"}
            </p>
            <div className="mt-1 flex items-center gap-2">
              {me.user ? (
                <>
                  <Badge variant="accent">GitHub · @{me.user.github_username}</Badge>
                </>
              ) : (
                <Badge variant="neutral">Shared-secret session</Badge>
              )}
            </div>
          </div>
        </div>

        <Section title="APPEARANCE">
          <Row label="Theme">
            <ThemeToggle />
          </Row>
        </Section>

        <Section title="DEPLOYMENT">
          <Row label="AI provider mode">
            <Badge variant="warning">mock</Badge>
          </Row>
          <Row label="Auth model">
            <span className="text-right text-foreground">
              Single-tenant, shared-secret + GitHub OAuth (equally privileged)
            </span>
          </Row>
          <Row label="Data">
            <span className="text-right text-foreground">Shared seeded demo corpus</span>
          </Row>
        </Section>

        <Section title="DOCUMENTATION">
          <div className="space-y-1.5 p-5 text-sm">
            <DocLink href="https://github.com/imraghavbansal/Kosma/blob/main/PRODUCT-SPEC.md">
              PRODUCT-SPEC.md - product thesis, V1 scope decisions
            </DocLink>
            <DocLink href="https://github.com/imraghavbansal/Kosma/blob/main/docs/architecture.md">
              docs/architecture.md - every major decision, with tradeoffs
            </DocLink>
            <DocLink href="https://github.com/imraghavbansal/Kosma/blob/main/docs/development-plan.md">
              docs/development-plan.md - phase-by-phase build plan
            </DocLink>
          </div>
        </Section>

        <div className="rounded-lg border border-danger/20 bg-danger/5 p-5">
          <p className="mb-1 text-sm font-medium text-foreground">Sign out</p>
          <p className="mb-3 text-xs text-muted">
            Ends this session. You can sign back in with GitHub or the shared secret
            any time.
          </p>
          <LogoutButton />
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-3 text-xs font-medium tracking-wider text-muted">{title}</p>
      <div className="divide-y divide-border rounded-lg border border-border bg-surface">{children}</div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between px-5 py-3 text-sm transition-colors duration-150 hover:bg-surface-2">
      <span className="text-muted">{label}</span>
      {children}
    </div>
  );
}

function DocLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="block text-accent transition-colors duration-150 hover:underline"
    >
      {children}
    </a>
  );
}
