import { redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatRelativeTime } from "@/lib/format";
import type { Agent } from "@/lib/types";
import Link from "next/link";
import { Badge } from "@/components/badge";
import { NewConfigForm } from "@/components/new-config-form";

export default async function AgentsPage() {
  const res = await serverApiFetch("/v1/agents");
  if (res.status === 401) redirect("/login");

  const agents: Agent[] = res.ok ? (await res.json()).items : [];

  return (
    <div className="p-8">
      <h1 className="font-mono text-xl text-foreground">Agents &amp; Configs</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Every agent Kosma knows about, and the prompt/model configs it can propose
        changes between.
      </p>

      {agents.length === 0 ? (
        <div className="mt-6 rounded-lg border border-dashed border-border p-6">
          <p className="text-sm text-muted">
            No agents yet -{" "}
            <Link href="/dashboard/projects" className="text-accent hover:underline">
              create a project
            </Link>{" "}
            to get a default agent automatically.
          </p>
        </div>
      ) : (
        <div className="mt-6 space-y-6">
          {agents.map((agent) => (
            <div key={agent.id} className="rounded-lg border border-border bg-surface">
              <div className="border-b border-border px-5 py-4">
                <p className="font-mono text-sm text-foreground">{agent.name}</p>
                {agent.description && <p className="mt-1 text-xs text-muted">{agent.description}</p>}
              </div>
              <div className="divide-y divide-border">
                {agent.configs.map((config) => (
                  <div
                    key={config.id}
                    className="flex items-center justify-between px-5 py-3 transition-colors duration-150 hover:bg-surface-2"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm text-foreground">{config.version_label}</span>
                        {config.is_baseline && <Badge variant="accent">baseline</Badge>}
                        <Badge variant="neutral">{config.kind}</Badge>
                      </div>
                      <p className="mt-1 text-xs text-muted">
                        {config.model_provider ?? "n/a"} / {config.model_name ?? "n/a"} - created{" "}
                        {formatRelativeTime(config.created_at)}
                      </p>
                      {config.prompt_text && (
                        <p className="mt-1.5 max-w-2xl truncate text-xs text-muted/80">
                          {config.prompt_text}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <div className="border-t border-border">
                <NewConfigForm agentId={agent.id} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
