---
doc_id: FLOW-REV-DAMAI-PARTIAL-20260924
title: 大麦物流演示数据部分实现审查
doc_type: review
status: open
version: 1.0
created_at: 2026-09-24
updated_at: 2026-09-24
last_reviewed_at: 2026-09-24
owner: FLOW
subject_ref: codex/damai-logistics-implementation@cd9c4b4
findings: [damai-source-substitution, review-service-bypass, canonical-dimension-collapse, release-drift, incomplete-cross-domain-seed, rollback-unverified]
applies_to: repository
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/superpowers/specs/2026-09-24-damai-logistics-demo-data-design.md
  - docs/superpowers/plans/2026-09-24-damai-logistics-demo-data-implementation-plan.md
evidence_refs:
  - codex/damai-logistics-implementation@cd9c4b4
confidentiality: project-internal
---

# 大麦物流演示数据部分实现审查

## 1. 结论

当前实现是“可生成、可通过部分单测的半成品”，不是可用来证明 FLOW 全系统
正常的完整 mock 数据方案。在 `cd9c4b4` 上，6 个大麦定向测试文件共 36 项全绿，
但测试没有捕捉数据替代、审核绕过和维度压缩。因此“测试通过”不等于“方案已验收”。
当前 dirty working tree 的发行包零漂移检查通过，但 head 与生成产物存在 5 个未提交差异；
`check_docs.py --phase m6` 因 4 个缺 frontmatter 的文档失败。

## 2. 已经完成

- 已建立 24 个连续月份的公司画像和规模锚；
- 已生成月度经营、财务、预算、AR、现金和 forecast sidecar 的基础数据；
- 已生成 FY2025/FY2026 合成财报和静态发行包；
- 已实现工作簿导入、12 个指标快照和 1 个 AnalysisRun 的部分 seed 链；
- 已复用固定 bootstrap enterprise UUID，没有创建第二个企业导致授权崩溃。

## 3. 阻断级问题

| 级别 | 问题 | 影响 | 必须修正 |
|---|---|---|---|
| P0 | loader 实际读取 `docs/implementation/p5/alibaba_*` | 页面中所谓“大麦财报”的行数据来自阿里巴巴文件 | 只能读取 `fixtures/damai/statements/*.yaml`，source SHA 也必须对应该合成文件 |
| P0 | loader 使用 `9988.HK` 冒充大麦身份 | 与真实阿里财报唯一身份/重述链重叠，`/operations` 也会读取阿里分部数据 | 使用 `DAMAI.SYN`、独立归一化映射和独立运营投影 |
| P0 | loader 直接 `report.status = "published"` | 绕过 `ReviewService.publish` 和质量门禁，无法证明审核链可用 | 必须先 normalize，再调用审核服务发布，最后才冻结 |
| P0 | profile 宣称 40 客户/8 产品/6 区域，canonical 却是 1/1/1 | 客户、产品、区域下钻与异常定位实际没有被验证 | 生成真实合成明细，禁止聚合成员代替规格声明 |
| P0 | `cd9c4b4` 之后的 working tree 有 5 个未提交生成产物差异 | head 与当前生成器输出不同源 | 以 `git diff -- fixtures/damai` 复核文件清单，确认生成器正确后重建并提交 |

## 4. 严重缺口

- canonical 只有 72 条经营实际、12 条收入预算、48 条 AR，无法覆盖客户、产品、
  区域和客群维度；
- AR 只有分析期 4 个桶，没有完整的 `current/1-30/31-60/61-90/90+` 五桶，
  也缺少分析引擎计算 AR/DSO 同比所需的比较期 12 个月；
- 预算只有集团收入，未覆盖直接成本、毛利、期间费用和经营利润；
- Finding/Evidence/Conclusion 状态机、内部冻结报告、客观快照、经营概览和
  发布/下载旅程尚未完成；
- 大麦 synthetic 指标覆盖数据集和前端切换尚未完成；
- 现有分析引擎只有 5 个 playbook，单次 AnalysisRun 不可能生成原计划声称的
  “至少 6 个系统 Finding”；额外异常只能作为可追溯信号/证据，或另立产品功能项；
- 不变量失败、第二份财报失败、freeze 失败的整体回滚没有证据；
- 没有从 `/data` 页面真实上传 XLSX 的 E2E，也没有八个页面的非空/下钻/证据验收；
- 没有当前精确 head SHA 的全量 CI 绿色证据。
- M6 当前因 `CODE_OF_CONDUCT.md`、`CONTRIBUTING.md`、`SECURITY.md` 和
  生成的 `fixtures/damai/README.md` 缺 frontmatter 而失败。

## 5. 完成定义

大麦发行版只有同时满足以下条件才能称为完成：

1. 两个连续完整财年（当期+同比）、全维度 canonical 数据和闭合四表通过不变量；
2. 同一静态发行包经真实工作簿导入、财报审核、分析、Finding 和冻结发布链装载；
3. 二次 seed 计数不增长，任一故障注入后全体回滚；
4. 主要页面都由同一企业/期间数据驱动，并通过真实上传、下钻、审核、冻结和下载 E2E；
5. 生成零漂移、全量回归、文档 M6 和同一最终 head SHA CI 全绿。
