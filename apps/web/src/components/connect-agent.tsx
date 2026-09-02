"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Agent } from "@/lib/types";

const TABS = ["Python SDK", "curl"] as const;
type Tab = (typeof TABS)[number];

export function ConnectAgent({ projectId, agents }: { projectId: string; agents: Agent[] }) {
  const [tab, setTab] = useState<Tab>("Python SDK");
  const [regenerating, setRegenerating] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const agent = agents[0];
  const config = agent?.configs[0];
  const agentId = agent?.id ?? "<AGENT_ID>";
  const configId = config?.id ?? "<AGENT_CONFIG_ID>";

  async function regenerate() {
    if (!confirm("This invalidates the current API key immediately. Continue?")) return;
    setRegenerating(true);
    try {
      const res = await apiFetch(`/v1/projects/${projectId}/regenerate-key`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setNewKey(data.api_key);
        setCopied(false);
      }
    } finally {
      setRegenerating(false);
    }
  }

  const pythonSnippet = `pip install git+https://github.com/imraghavbansal/Kosma.git#subdirectory=packages/sdk

export KOSMA_API_KEY="<your project's API key>"
export KOSMA_API_URL="https://kosma-wb46.onrender.com"

from kosma import tracer

with tracer.start_trace(
    "${agent?.name ?? "my-agent"}",
    agent_id="${agentId}",
    agent_config_id="${configId}",
    workflow_tag="refund",
    input_text="the request your agent received",
) as t:
    t.set_model("openai", "gpt-4o-mini")

    with t.span("generate_response", span_type="llm") as gen:
        answer = run_your_agent(...)
        gen.set_output(answer=answer)

    t.set_usage(input_tokens=180, output_tokens=64)
    t.set_success(True)

print(t.trace_id)  # real trace, now visible in Kosma`;

  const curlSnippet = `curl -X POST https://kosma-wb46.onrender.com/v1/traces \\
  -H "Authorization: Bearer <your project's API key>" \\
  -H "Content-Type: application/json" \\
  -d '{
    "trace_ref": "unique-id-per-call",
    "agent_id": "${agentId}",
    "agent_config_id": "${configId}",
    "input_text": "what your agent received",
    "success": true,
    "latency_ms": 420,
    "input_tokens": 120,
    "output_tokens": 80
  }'`;

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-medium text-foreground">Connect your agent</p>
        <div className="flex overflow-hidden rounded-md border border-border">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-2.5 py-1 text-[11px] font-medium transition-colors duration-150 ${
                tab === t ? "bg-accent text-accent-foreground" : "bg-surface-2 text-muted hover:text-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <pre className="overflow-x-auto rounded-md border border-border bg-background p-3 font-mono text-[11px] leading-relaxed text-foreground/90">
        {tab === "Python SDK" ? pythonSnippet : curlSnippet}
      </pre>

      {!agent && (
        <p className="mt-2 text-[10px] text-warning">
          This project has no agent yet - agent_id/agent_config_id above are placeholders.
        </p>
      )}

      <div className="mt-3 flex items-center gap-3 border-t border-border pt-3">
        <p className="text-[11px] text-muted">Lost your API key?</p>
        <button
          onClick={regenerate}
          disabled={regenerating}
          className="text-[11px] font-medium text-accent transition-colors duration-150 hover:underline disabled:opacity-40"
        >
          {regenerating ? "Regenerating..." : "Regenerate it"}
        </button>
      </div>

      {newKey && (
        <div className="animate-fade-in mt-3 rounded-md border border-warning/30 bg-warning/5 p-3">
          <p className="mb-2 text-[11px] text-warning">
            New key - copy it now, the old one no longer works and this won&apos;t be shown again.
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 overflow-x-auto whitespace-nowrap font-mono text-[11px] text-foreground">
              {newKey}
            </code>
            <button
              onClick={() => {
                navigator.clipboard.writeText(newKey);
                setCopied(true);
              }}
              className="shrink-0 rounded-md border border-border px-2 py-1 text-[11px] text-foreground transition-colors duration-150 hover:bg-surface-2"
            >
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
