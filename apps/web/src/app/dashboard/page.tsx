export default function DashboardHome() {
  return (
    <div className="p-8">
      <h1 className="font-mono text-xl text-foreground">Propose a Change</h1>
      <p className="mt-2 max-w-xl text-sm text-muted">
        This is the TraceOS home screen: instead of a trace list, it will let you propose
        a prompt or model change, run it against a matched historical cohort, and see the
        Blast Radius Diff before you ship anything.
      </p>
      <div className="mt-8 rounded-lg border border-dashed border-border p-6">
        <p className="text-sm text-muted">
          Foundation phase only — the change engine (Phases 5-7) isn&apos;t wired up yet.
          Once it is, this screen becomes the propose-change flow described in{" "}
          <code className="rounded bg-surface px-1 py-0.5 font-mono text-xs">
            PRODUCT-SPEC.md
          </code>
          .
        </p>
      </div>
    </div>
  );
}
