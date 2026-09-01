import Link from "next/link";

type InvestigationPageProps = {
  params: Promise<{ findingId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

function first(value: string | string[] | undefined): string {
  return Array.isArray(value) ? (value[0] ?? "未提供") : (value ?? "未提供");
}

export default async function InvestigationPage({ params, searchParams }: InvestigationPageProps) {
  const [{ findingId }, query] = await Promise.all([params, searchParams]);
  const identities = [
    ["Finding ID", findingId],
    ["数据批次 ID", first(query.batch_id)],
    ["指标快照 ID", first(query.metric_snapshot_id)],
    ["分析运行 ID", first(query.analysis_run_id)],
  ];

  return (
    <main className="investigation-shell">
      <Link className="investigation-shell__back" href="/" aria-label="返回经营驾驶舱">← 返回经营驾驶舱</Link>
      <section className="investigation-receipt">
        <p className="eyebrow">FLOW · INVESTIGATION HANDOFF</p>
        <h1>经营调查上下文</h1>
        <p className="investigation-receipt__lead">
          此页面已接收驾驶舱发现及其不可变数据血缘，确保下一阶段的证据审阅不会脱离原始分析语境。
        </p>
        <dl role="region" aria-label="不可变分析上下文">
          {identities.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
        <div className="investigation-receipt__next" role="status">
          <strong>调查工作台将在下一阶段展开</strong>
          <span>Phase 6 仅验证上下文交接；证据审阅、结论确认与行动闭环属于 Phase 7。</span>
        </div>
      </section>
    </main>
  );
}
