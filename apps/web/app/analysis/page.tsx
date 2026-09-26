import { FourQuestionWorkbench } from "../../components/analysis/four-question-workbench";
import { AppShell } from "../../components/shell/app-shell";

export const metadata = { title: "四问工作台 | FLOW" };

function first(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

export default async function AnalysisPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  const runId = first(query.run_id);
  return (
    <AppShell>
      {/* key 随深链参数变化强制重挂载，清空定位等会话态（同批次一模式） */}
      <FourQuestionWorkbench key={runId ?? ""} initialRunId={runId} />
    </AppShell>
  );
}
