import { ReportsCenter } from "../../components/reports/reports-center";
import { AppShell } from "../../components/shell/app-shell";

export const metadata = { title: "报告中心 | FLOW" };

function first(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

export default async function ReportsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  return (
    <AppShell>
      <ReportsCenter initialSnapshot={first(query.snapshot)} initialFocus={first(query.focus)} />
    </AppShell>
  );
}
