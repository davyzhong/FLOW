import { AppShell } from "../../components/shell/app-shell";
import { OperationsOverviewApp } from "../../components/operations/operations-overview";

export const metadata = { title: "经营概览 | FLOW" };

function first(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

export default async function OperationsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  return (
    <AppShell>
      <OperationsOverviewApp initialReportId={first(query.report)} />
    </AppShell>
  );
}
