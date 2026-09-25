import { AppShell } from "../../components/shell/app-shell";
import { StatementApp } from "../../components/statements/statement-app";

export const metadata = { title: "报表分析 | FLOW" };

function first(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

export default async function StatementsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  return (
    <AppShell>
      <StatementApp initialReportId={first(query.report)} />
    </AppShell>
  );
}
