# FLOW Phase 5 验证记录

验证日期：2026-09-01

功能实现提交：`83b3631`

CI 门禁提交：`fb10d8b`

CI 集成环境修复提交：`91bfca4`

分析策略集：`flow.analysis.logistics.v1`

分析引擎：`flow-analysis/1`

## 结论

Phase 5“Analysis & Findings”已完成本地与 GitHub Actions 验收。FLOW 现在可以从一个已发布 Metric Snapshot 及其绑定的 canonical 明细，生成不可变、可重现的 Analysis Run。首版分析层包含 5 个有类型的物流经营分析 Playbook、严格对账的 Driver Contributions、4 个通过硬门槛的确定性 Finding，以及完整证据和透明评分分解。

页面、AI 和报告无需也不得重新计算这些结果。缺字段或无法匹配的分析会明确降级，不会用假设补齐，更不会产生推测性 Finding。

## 验收门禁

| 命令或检查 | 结果 | 证据摘要 |
|---|---|---|
| `make test-analysis-invariants` | PASS | 39 个分析/集成/降级测试、42 个指标回归、1 个 Intake E2E、Ruff、mypy、迁移完整往返和机器摘要全部通过 |
| 分析专项测试 | PASS | 5 个 Playbook 的精确 oracle、桥接对账、Finding 硬门槛、排名、证据、幂等、不可变和事务回滚均通过 |
| 上游回归 | PASS | Phase 4 已知答案 42 个测试通过；Phase 3 Intake E2E 通过 |
| `make test-api` | PASS | 202 个 API、domain、integration、数据契约和分析测试全部通过，耗时 339.32 秒 |
| 全量 integration | PASS | 在执行 `alembic upgrade head` 后 54 个测试全部通过，耗时 286.97 秒 |
| Web 测试 | PASS | 2 个 Vitest 测试通过 |
| 合约检查 | PASS | OpenAPI → TypeScript 再生成后无差异 |
| 数据库迁移 | PASS | 隔离 schema 中 `base → 0007 → base → 0007` 完整往返通过 |
| 静态检查 | PASS | Ruff、ESLint 无问题；mypy 检查 78 个源码文件无问题；TypeScript `tsc --noEmit` 通过 |
| GitHub Actions | PASS | 修复提交的 FLOW CI 11 个 jobs 全部通过，包含 `analysis-invariants` 和执行迁移后的全量 `integration`；运行 [33460145782](https://github.com/davyzhong/FLOW/actions/runs/33460145782) |

## 冻结的机器摘要

```json
{
  "status": "PASS",
  "policy_id": "flow.analysis.logistics.v1",
  "policy_hash": "448b390877b20090af02f6584e79a1c9796fe5ab0a5c9aeb784f6ab497e94f5a",
  "engine_version": "flow-analysis/1",
  "result_count": 5,
  "complete_results": [
    "ar_cash_impact",
    "fulfillment_cost_rve",
    "gross_profit_bridge",
    "operating_profit_bridge",
    "revenue_vpm"
  ],
  "degradation_scenarios": [
    "unmatched_mix_cell",
    "missing_required_field"
  ]
}
```

冻结答案保存在 `fixtures/expected/analysis_results_v1.json`。`scripts/summarize_analysis.py` 直接读取独立 known-answer oracle 和版本化策略输出摘要；专项门禁还会将持久化结果逐项与该 oracle 比较，因此摘要不是对生产计算器的循环自证。

## 关键分析答案

### 五个 Analysis Results

| Playbook | 影响金额（CNY） | 关键 Driver Contributions |
|---|---:|---|
| Revenue V/P/M | 2,356,634.0957 | Volume 1,467,228.4924；Mix 0.1272；Price 889,405.4761 |
| Fulfillment Cost R/V/E | 2,103,605.1451 | Volume 934,003.9796；Efficiency -0.0899；Rate 1,169,601.2555 |
| Gross Profit Bridge | 253,028.9506 | 收入 V/P/M 与仓储、运输、其他直接成本变化共同对账 |
| Operating Profit Bridge | -77,484.3599 | 毛利桥贡献减经营费用变化 |
| AR Cash Impact | -365,415.0177 | 账龄桶余额变化的负向现金影响合计 |

所有 Driver Contributions 与对应影响金额在 `0.01 CNY` 容差内严格对账。Revenue V/P/M 和履约成本桥保留数学驱动标签，不把价格、效率或费率变化扩写成缺乏业务证据的因果判断。

### Finding 排名

| 排名 | Finding 类型 | 总分 |
|---:|---|---:|
| 1 | `fulfillment_cost_increase` | 87.000000 |
| 2 | `revenue_growth` | 82.000000 |
| 3 | `ar_cash_deterioration` | 64.616601 |
| 4 | `operating_profit_deterioration` | 53.099374 |

每个 Finding 保存 materiality、persistence、evidence completeness 和 management relevance 四项分数以及合计公式。每个 Finding 有 5 个已验证 Evidence 对象。T12 毛利变化为正，因此系统没有错误地产生 `gross_profit_deterioration`。

## 已证明的分析不变量

- 分析只接受已发布 Metric Snapshot，并且 canonical repository 必须绑定同一个已发布 Import Version；
- 分析策略文档经规范化后生成稳定哈希，Analysis Run 身份由 `metric_snapshot_id + policy_set_hash + engine_version` 构成；
- Revenue V/P/M、履约成本 R/V/E、毛利桥、经营利润桥和 AR 现金影响均使用 `Decimal` 并保存精确计算轨迹；
- complete bridge 的 Driver Contributions 必须与影响金额在策略容差内对账，否则不得发布；
- Finding 只有在分析 complete、桥接已对账、超过 materiality、证据齐全且政策允许时才生成；
- 相同身份重试返回同一已发布 Analysis Run，不复制子对象；
- Analysis Run、Result、Driver、Finding、Score 和 Evidence 在发布后不可更新或删除；
- 写入中途故障会回滚整个运行，不留下部分发布对象；
- 新增或丢失产品导致 V/P/M mix cell 无法匹配时，结果显式标记为 `degraded`；
- 缺少 AR 必需字段时，AR 分析显式降级；两种情况都不生成相应 Finding。

## 持久化对象与消费边界

迁移 `0007_add_analysis_runs` 新增 Analysis Run、Result、Driver 和 Score 持久化对象，并扩展 Finding 与 Evidence 的分析身份和证据引用。Analysis Service 在单一事务内运行注册表中的全部 Playbook、构建合格 Findings 与 Evidence，最后将 run 原子切换为 `published`。

Phase 6 及以后只能读取已发布 Analysis Run：

- Dashboard 展示同一批已排名 Findings 和桥接结果；
- Investigation 展开相同 Driver、Evidence、公式和来源；
- AI 只解释已有事实和证据，不生成金额或排名；
- PPT、Excel 和正式月报引用同一已批准分析对象。

## CI 环境差异与修复

本地首次执行完整专项门禁时，Alembic 子进程没有继承项目本地开发数据库默认环境，导致迁移入口无法连接。`scripts/test_analysis_invariants.sh` 随后为未显式提供的开发变量设置与既有 Make 门禁一致的默认值，同时保留 CI 或调用方覆盖能力。修复后同一命令完整通过。

功能门禁提交 `fb10d8b` 的 GitHub Actions 运行 [33458950559](https://github.com/davyzhong/FLOW/actions/runs/33458950559) 中，10 个 jobs 通过，但旧 `integration` job 在空 PostgreSQL 上直接运行测试，没有先执行 migration。此前的集成测试未触及完整 canonical 表，因此这个隐含环境依赖直到 Phase 5 新测试 fixture 清理 `fact_ar_collection` 时才暴露。

修复提交 `91bfca4` 在 `integration` job 中显式执行 `alembic upgrade head`。本地按 CI 环境变量复现相同序列后，54 个 integration tests 全部通过。失败运行被保留为过程证据，没有删除或重写历史。

修复后的 GitHub Actions 运行 [33460145782](https://github.com/davyzhong/FLOW/actions/runs/33460145782) 最终 11 个 jobs 全部通过。

## 已知边界

- V1 的五个 Playbook 当前使用 T12 对齐上年同期比较，月度/YTD/预算桥可以在相同协议下扩展，但尚未实现；
- persistence 组件已经进入评分协议；当前单个运行没有跨月连续异常历史，使用策略定义的中性分 50，而不是声称已证明持续性；
- Findings 是确定性候选，尚未包含 Phase 7 的人工复核、批准和结论工作流；
- AR cash impact 是应收增加的估算营运资金现金影响，不等同于也不宣称完全解释经营现金流变化；
- Phase 5 没有 API 路由或页面；Dashboard 属于 Phase 6，Investigation 属于 Phase 7；
- Forecast、情景、建议、行动责任人和截止日期不在本阶段范围。

## 下一阶段入口

Phase 6“Finance BP Dashboard”应以已发布 Metric Snapshot 和 Analysis Run 作为唯一经营数字边界，落实已批准的高信息密度首页：当月/YTD 核心指标、趋势、利润桥、按影响排序的 Findings、客户群×物流产品矩阵和 Investigation 跳转。浏览器不得读取原始文件接口，也不得自行计算指标、Driver 或 Finding 排名。
