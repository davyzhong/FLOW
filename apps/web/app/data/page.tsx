import { DataWorkbench } from "../../components/data/data-workbench";
import { AppShell } from "../../components/shell/app-shell";

export const metadata = { title: "数据工作台 | FLOW" };

function first(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

export default async function DataPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  return (
    <AppShell>
      <DataWorkbench initialBatchId={first(query.batch)} />
    </AppShell>
  );
}
