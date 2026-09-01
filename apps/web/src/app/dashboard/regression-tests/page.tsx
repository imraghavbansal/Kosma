import { redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatRelativeTime } from "@/lib/format";
import type { RegressionTest } from "@/lib/types";
import { Badge } from "@/components/badge";

export default async function RegressionTestsPage() {
  const res = await serverApiFetch("/v1/regression-tests");
  if (res.status === 401) redirect("/login");

  const tests: RegressionTest[] = res.ok ? (await res.json()).items : [];

  return (
    <div className="p-8">
      <h1 className="font-mono text-xl text-foreground">Regression Tests</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Generated from the worst regressions a change analysis found - inputs that
        succeeded under the baseline config and failed under the candidate during
        replay. Execution itself is a future step; these are the specs.
      </p>

      {tests.length === 0 ? (
        <div className="mt-6 rounded-lg border border-dashed border-border p-6">
          <p className="text-sm text-muted">
            None yet. Generate a suite from a change proposal&apos;s impact report once
            it flags a regression.
          </p>
        </div>
      ) : (
        <div className="mt-6 overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-2 text-left text-xs text-muted">
                <th className="px-4 py-2.5 font-medium">Input</th>
                <th className="px-4 py-2.5 font-medium">Expected condition</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="px-4 py-2.5 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {tests.map((test) => (
                <tr key={test.id} className="border-b border-border last:border-0 hover:bg-surface-2">
                  <td className="max-w-xs truncate px-4 py-2.5 text-xs text-foreground">
                    {test.input_text}
                  </td>
                  <td className="max-w-md truncate px-4 py-2.5 text-xs text-muted">
                    {test.expected_condition}
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge variant={test.status === "pending" ? "warning" : "neutral"}>
                      {test.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 text-xs text-muted">{formatRelativeTime(test.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
