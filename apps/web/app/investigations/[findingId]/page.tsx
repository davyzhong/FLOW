import type { Metadata } from "next";

import { InvestigationApp } from "../../../components/investigation/investigation-app";

export const metadata: Metadata = {
  title: "FLOW · 经营调查",
  description: "证据优先的经营调查与复核工作台",
};

function first(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

export default async function InvestigationPage({
  params,
  searchParams,
}: {
  params: Promise<{ findingId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [{ findingId }, query] = await Promise.all([params, searchParams]);
  return (
    <InvestigationApp
      query={{
        finding_id: findingId,
        batch_id: first(query.batch_id),
        metric_snapshot_id: first(query.metric_snapshot_id),
        analysis_run_id: first(query.analysis_run_id),
      }}
    />
  );
}
