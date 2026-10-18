import type { DashboardResponse } from "../../lib/api/client";
import { FlowIcon } from "./icons";
import { formatFinancialValue } from "../cockpit/number-format";

export function FindingsPanel({ findings }: { findings: DashboardResponse["findings"] }) {
  return (
    <section className="panel findings-panel" aria-label="重点经营发现">
      <div className="panel-heading"><div><span>04</span><h3>重点经营发现</h3></div><small>按影响与证据评分排序</small></div>
      <ol>{findings.map((finding, index) => <li key={finding.finding_id}>
        <span className="finding-rank">{String(index + 1).padStart(2, "0")}</span>
        <div><h4><a className="finding-title-link" href={finding.investigation_path}>{finding.title}</a></h4><p>影响 <strong className={`is-${finding.impact.semantic_direction}`}>{formatFinancialValue(finding.impact.exact_value, { unit: "CNY" })}</strong> · 证据 {finding.evidence_verified}/{finding.evidence_total} · 得分 {finding.total_score}</p></div>
        <a href={finding.investigation_path} aria-label={`${finding.title}：进入调查`}>进入调查 <FlowIcon name="arrow" /></a>
      </li>)}</ol>
    </section>
  );
}
