"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { CountUp } from "@/components/count-up";

type ApiStatus = "checking" | "online" | "offline";

export function SidebarStatus() {
  const [status, setStatus] = useState<ApiStatus>("checking");
  const [traces, setTraces] = useState<number | null>(null);
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const clock = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(clock);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function ping() {
      try {
        const res = await apiFetch("/v1/public/stats");
        if (cancelled) return;
        if (res.ok) {
          const data = await res.json();
          setTraces(data.total_traces);
          setStatus("online");
        } else {
          setStatus("offline");
        }
      } catch {
        if (!cancelled) setStatus("offline");
      }
    }

    ping();
    const interval = setInterval(ping, 60_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="relative mt-6 overflow-hidden rounded-lg border border-border bg-surface px-3 py-3">
      <div className="bg-grid bg-glow pointer-events-none absolute inset-0 opacity-[0.35]" />
      <div className="starfield" aria-hidden="true" />
      <div className="relative z-10 space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-[10px] font-medium tracking-wider text-muted">
            <StatusDot status={status} />
            API {status === "checking" ? "checking..." : status}
          </span>
          <span className="font-mono text-[10px] text-muted">
            {now
              ? now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
              : "--:--:--"}
          </span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-[10px] text-muted">Traces recorded</span>
          <span className="font-mono text-sm text-foreground">
            {traces !== null ? <CountUp value={traces} /> : "--"}
          </span>
        </div>
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: ApiStatus }) {
  if (status === "checking") {
    return <span className="h-1.5 w-1.5 rounded-full bg-muted" />;
  }
  if (status === "offline") {
    return <span className="h-1.5 w-1.5 rounded-full bg-danger" />;
  }
  return <span className="glow-pulse h-1.5 w-1.5 rounded-full bg-success" />;
}
