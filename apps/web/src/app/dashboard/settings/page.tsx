import { redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { Badge } from "@/components/badge";

export default async function SettingsPage() {
  const meRes = await serverApiFetch("/v1/auth/me");
  if (meRes.status === 401) redirect("/login");
  const me = meRes.ok ? await meRes.json() : { user: null };

  return (
    <div className="p-8">
      <h1 className="font-mono text-xl text-foreground">Settings</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        This deployment&apos;s configuration - read-only for now, matching V1&apos;s
        single-tenant scope (see PRODUCT-SPEC.md).
      </p>

      <div className="mt-6 space-y-6">
        <Section title="SESSION">
          <Row label="Signed in as">
            {me.user ? (
              <div className="flex items-center gap-2">
                {me.user.avatar_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={me.user.avatar_url}
                    alt={me.user.github_username}
                    className="h-5 w-5 rounded-full ring-1 ring-border"
                  />
                )}
                <span className="text-foreground">
                  {me.user.display_name ?? me.user.github_username}
                </span>
                <Badge variant="accent">GitHub</Badge>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-foreground">Shared secret</span>
                <Badge variant="neutral">shared session</Badge>
              </div>
            )}
          </Row>
        </Section>

        <Section title="DEPLOYMENT">
          <Row label="AI provider mode">
            <Badge variant="warning">mock</Badge>
          </Row>
          <Row label="Auth model">
            <span className="text-foreground">
              Single-tenant, shared-secret + GitHub OAuth (both equally privileged)
            </span>
          </Row>
          <Row label="Data">
            <span className="text-foreground">Shared seeded demo corpus - clearly labeled throughout</span>
          </Row>
        </Section>

        <Section title="DOCUMENTATION">
          <div className="space-y-1.5 text-sm">
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
