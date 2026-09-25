import { AppShell } from "../../components/shell/app-shell";
import { MetricLibraryApp } from "../../components/metric-library/metric-library-app";

export const metadata = { title: "指标库 | FLOW" };

function first(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

export default async function MetricLibraryPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  const focus = first(query.focus);
  const entry = first(query.entry);
  return (
    <AppShell>
      {/* key 随深链参数变化强制重挂载，清空定位/筛选等会话态 */}
      <MetricLibraryApp key={`${focus ?? ""}|${entry ?? ""}`} focus={focus} entry={entry} />
    </AppShell>
  );
}
