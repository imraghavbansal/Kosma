export function PlaceholderPage({ title, phase }: { title: string; phase: string }) {
  return (
    <div className="p-8">
      <h1 className="font-mono text-xl text-foreground">{title}</h1>
      <div className="mt-8 rounded-lg border border-dashed border-border p-6">
        <p className="text-sm text-muted">Not yet implemented. Arrives in {phase}.</p>
      </div>
    </div>
  );
}
