# 文档适用性与历史证据索引

核对日期：2026-09-04；代码基线：`c1a59d1`。当前阅读入口见[文档导航](README.md)。本表逐份覆盖 `docs/superpowers/plans/`、`docs/superpowers/specs/`、`docs/implementation/` 和 `docs/reviews/` 的 Markdown，原始研究、会话与图片档案不在本表改写范围。本文是文档状态核对，不是新一轮全量功能测试。

## 当前与历史的边界

- V1 正式规格及 Phase 5/6 设计继续作为契约依据，产品范围以 D039 的客观财务分析为准，推进顺序以 D038 为准。
- Phase 1–10 的功能切片和 Pilot Phase 1 有历史实现/门禁证据。历史测试数量、命令输出和 CI 快照不自动延续为当前提交的绿色证据。
- Pilot Phase 2 仅 A/B 认证入口已实现；C–G 部署、备份恢复、日志及全阶段出口门禁仍需执行。单用户认证通过不等于生产就绪。
- `6f6b401` 证明基线修复已有实质交付；本地 tag 未见 `v0.1.1`，不宣布原计划 Task 5 完成。`v0.2-pilot-baseline` 指向 `f5549cb` 的历史 Pilot 1 证据，不是当前提交验收证明。
- 最新修复验收保留真实对象存储上传超时/未通过的边界；存储替身测试和真实认证链路分别记录，不能合并为完整生产链路成功。

## 已修复审查条目

问题原文见[首轮审查](reviews/2026-09-04-project-code-review.md)及[同步后复审](reviews/2026-09-04-synced-project-code-review.md)，修复、验证及迁移兼容细节以[修复验收](implementation/2026-09-04-review-repairs.md)为准。

| 条目 | 内容 | 修复提交 |
| --- | --- | --- |
| R1–R3 | 冻结内容、签发资格、持久化人工映射 | `fa171ec` |
| R4–R9 | SHA、警告确认、Copilot 审计/批次、PPT 正文、下载名称 | `e688f1b` |
| N2 | OpenAPI/TypeScript 合约同步 | `e688f1b` |
| N1/N3 | 登录会话与受保护代理、unit CI 隔离 | `c1a59d1` |

## 逐份文档登记

原计划 checklist、历史代码样例和验收数据按原语境保留；顶部说明指明后续变化，不机械补勾计划步骤。

| 文档 | 分类 | 保留与使用理由 |
| --- | --- | --- |
| [2026-08-30-flow-v1-master-roadmap.md](superpowers/plans/2026-08-30-flow-v1-master-roadmap.md) | 持续适用的分期基线 | 本路线图保留 V1 Phase 1–10 原始分期；功能窄切片已交付，Phase 10 的部署、备份恢复和深度可观测性按 D038 转入 Pilot Readiness。当前为 Pilot Phase 2 部分完成，不应从历史任务列表推断生产就绪。 |
| [2026-08-30-flow-v1-phase-1-foundation.md](superpowers/plans/2026-08-30-flow-v1-phase-1-foundation.md) | 历史实施计划 | Phase 1 功能切片已有实现与[阶段验收](implementation/phase-1-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。 |
| [2026-08-30-flow-v1-phase-2-data-contract.md](superpowers/plans/2026-08-30-flow-v1-phase-2-data-contract.md) | 历史实施计划 | Phase 2 功能切片已有实现与[阶段验收](implementation/phase-2-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。 |
| [2026-08-30-flow-v1-phase-3-intake.md](superpowers/plans/2026-08-30-flow-v1-phase-3-intake.md) | 历史实施计划 | Phase 3 功能切片已有实现与[阶段验收](implementation/phase-3-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。 接入映射、审批资格、Copilot 审计或冻结报告相关实现以本次修复验收为补充。 |
| [2026-08-30-flow-v1-phase-4-metrics.md](superpowers/plans/2026-08-30-flow-v1-phase-4-metrics.md) | 历史实施计划 | Phase 4 功能切片已有实现与[阶段验收](implementation/phase-4-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。 |
| [2026-08-30-flow-v1-phase-6-dashboard.md](superpowers/plans/2026-08-30-flow-v1-phase-6-dashboard.md) | 历史实施计划 | Phase 6 功能切片已有实现与[阶段验收](implementation/phase-6-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。 |
| [2026-09-01-flow-v1-phase-5-analysis.md](superpowers/plans/2026-09-01-flow-v1-phase-5-analysis.md) | 历史实施计划 | Phase 5 功能切片已有实现与[阶段验收](implementation/phase-5-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。 |
| [2026-09-02-flow-pilot-readiness-phase-1-user-closure.md](superpowers/plans/2026-09-02-flow-pilot-readiness-phase-1-user-closure.md) | 历史实施计划 | Pilot Phase 1 已有[历史出口门禁记录](implementation/phase-pilot-1-user-closure.md)，用户闭环实现及后续发现的映射、警告确认、冻结和下载问题已有补修。原始步骤保留；历史门禁通过不等于当前真实对象存储发布链路已通过验收。 |
| [2026-09-02-flow-v0.1.1-baseline-repair.md](superpowers/plans/2026-09-02-flow-v0.1.1-baseline-repair.md) | 历史实施计划 | 基线修复提交 `6f6b401` 已落地 manifest 排除自身、Markdown 生成清理、状态补证及 publishing-golden CI 等改动；公众号流水线随后移交 DavyBase，原计划脚本路径不再是当前执行入口。未发现本地 `v0.1.1` tag（现有 `v0.1.0`、`v0.2-pilot-baseline`），不能把 Task 5 发布或全计划标为完成；保留原 checkbox 作为历史计划。 |
| [2026-09-02-flow-v1-phase-7-investigation.md](superpowers/plans/2026-09-02-flow-v1-phase-7-investigation.md) | 历史实施计划 | Phase 7 功能切片已有实现与[阶段验收](implementation/phase-7-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。 接入映射、审批资格、Copilot 审计或冻结报告相关实现以本次修复验收为补充。 |
| [2026-09-02-flow-v1-phase-8-copilot.md](superpowers/plans/2026-09-02-flow-v1-phase-8-copilot.md) | 历史实施计划 | Phase 8 功能切片已有实现与[阶段验收](implementation/phase-8-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。 接入映射、审批资格、Copilot 审计或冻结报告相关实现以本次修复验收为补充。 |
| [2026-09-02-flow-v1-phase-9-publishing.md](superpowers/plans/2026-09-02-flow-v1-phase-9-publishing.md) | 历史实施计划 | Phase 9 功能切片已有实现与[阶段验收](implementation/phase-9-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。 接入映射、审批资格、Copilot 审计或冻结报告相关实现以本次修复验收为补充。 |
| [2026-09-03-flow-pilot-readiness-phase-2-security-deployment.md](superpowers/plans/2026-09-03-flow-pilot-readiness-phase-2-security-deployment.md) | 当前计划：部分完成 | 本计划仍是当前推进依据，但仅 Task A/B 的 API 认证及浏览器登录会话已实现并有定向验收；以[认证运行说明](operations/authentication.md)中的配置与实际路由行为为准。Task C–G（密钥与部署加固、备份恢复、日志、完整出口门禁及阶段证据）尚未完成；`make test-security-deployment-e2e` 仍是计划目标，不能直接当作现有命令。 |
| [2026-09-04-review-repairs.md](superpowers/plans/2026-09-04-review-repairs.md) | 已完成修复计划 | 本计划 R1–R9 已实施；随后追加 N1–N3 亦已修复。正文任务记录保留，不能将已关闭缺陷重新列为待实现范围。 |
| [2026-08-29-flow-v1-design.md](superpowers/specs/2026-08-29-flow-v1-design.md) | 有效设计基线 | 正式 V1 规格仍是架构与对象契约基线；产品定位按较晚决策 D039 聚焦客观财务分析，主观经营归因属未来扩展，确定性 V/P/M 与 R/V/E 保留。交付顺序及生产就绪边界按 D038；设计中的目标与原型表述不等于当前生产能力。 |
| [2026-09-01-flow-v1-phase-5-analysis-design.md](superpowers/specs/2026-09-01-flow-v1-phase-5-analysis-design.md) | 有效设计基线 | 本设计的已批准对象边界、财务口径与交互约束继续适用，对应 Phase 已实现；正文的实施前状态和后续阶段描述保留历史语境，不代表当前开发排期或生产部署认证。 |
| [2026-09-01-flow-v1-phase-6-dashboard-design.md](superpowers/specs/2026-09-01-flow-v1-phase-6-dashboard-design.md) | 有效设计基线 | 本设计的已批准对象边界、财务口径与交互约束继续适用，对应 Phase 已实现；正文的实施前状态和后续阶段描述保留历史语境，不代表当前开发排期或生产部署认证。 |
| [2026-09-04-review-repairs-design.md](superpowers/specs/2026-09-04-review-repairs-design.md) | 有效设计基线 | R1–R9 修复设计已实施；N1–N3 的追加实现与验证记录见修复验收。原设计继续约束冻结内容、审批资格、映射身份及财务口径。 |
| [2026-09-04-review-repairs.md](implementation/2026-09-04-review-repairs.md) | 当前修复验收 | 保留正文：记录 R1–R9/N1–N3、迁移兼容与真实对象存储限制。 |
| [phase-1-verification.md](implementation/phase-1-verification.md) | 历史验收证据 | 本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 |
| [phase-10-acceptance.md](implementation/phase-10-acceptance.md) | 历史验收证据 | 本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 功能组合门禁与生产就绪须分开；文末更正基线发版条件是历史要求，不能据此推断存在 `v0.1.1` 发布。 |
| [phase-2-verification.md](implementation/phase-2-verification.md) | 历史验收证据 | 本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 |
| [phase-3-verification.md](implementation/phase-3-verification.md) | 历史验收证据 | 本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 人工覆盖映射的恢复及前端警告确认属于后续补修，不由本阶段自动映射门禁单独证明。 |
| [phase-4-verification.md](implementation/phase-4-verification.md) | 历史验收证据 | 本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 |
| [phase-5-verification.md](implementation/phase-5-verification.md) | 历史验收证据 | 本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 |
| [phase-6-dashboard-fidelity.md](implementation/phase-6-dashboard-fidelity.md) | 历史验收证据 | 本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 |
| [phase-6-verification.md](implementation/phase-6-verification.md) | 历史验收证据 | 本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 |
| [phase-7-verification.md](implementation/phase-7-verification.md) | 历史验收证据 | 本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 批准后证据拒绝、结论修改退回复核与冻结资格的并发约束已在后续修复补强。 |
| [phase-8-verification.md](implementation/phase-8-verification.md) | 历史验收证据 | 本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 成功交互审计持久化及报告大纲批次选择已在后续修复补强。 |
| [phase-9-verification.md](implementation/phase-9-verification.md) | 历史验收证据 | 本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 文末待补的报告 API/下载已在 Pilot Phase 1 落地；冻结内容持久化、存储对象与 PPT 正文等后续修复以最新验收为准。PDF 魔数/体积检查不等于逐项提取 PDF 文本验证。 |
| [phase-pilot-1-user-closure.md](implementation/phase-pilot-1-user-closure.md) | 历史验收证据 | 本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 Pilot Phase 1 的实现和历史门禁已交付；后续审查发现的跨步骤缺陷另有补修。最新真实对象存储发布验收仍有限制。 |
| [2026-09-04-project-code-review.md](reviews/2026-09-04-project-code-review.md) | 已关闭问题的历史审查 | 本文是修复前代码的审查快照，保留原问题、行号、测试失败和当时 CI 结果。R1–R9 及追加 N1–N3 已分别由 `fa171ec`、`e688f1b`、`c1a59d1` 修复，不再是当前待修缺陷；历史 CI 状态不代表当前提交。真实 S3 发布链路、Pilot Phase 2 剩余部署工作和真实数据试点仍须单独验收。 |
| [2026-09-04-synced-project-code-review.md](reviews/2026-09-04-synced-project-code-review.md) | 已关闭问题的历史审查 | 本文是修复前代码的审查快照，保留原问题、行号、测试失败和当时 CI 结果。R1–R9 及追加 N1–N3 已分别由 `fa171ec`、`e688f1b`、`c1a59d1` 修复，不再是当前待修缺陷；历史 CI 状态不代表当前提交。真实 S3 发布链路、Pilot Phase 2 剩余部署工作和真实数据试点仍须单独验收。 |

共登记 33 个 Markdown：其中最新修复验收原文保留，其余添加适用性说明；Pilot Phase 1 文档另更正已落地 CI job 的过期待办。原始图片不作修改。

## 其余项目文档的处理范围

| 文档组 | 本轮处理 |
| --- | --- |
| 根 README、docs/README、API 索引 | 以 c1a59d1 重建当前产品与工程入口 |
| architecture、data-contract、intake、metrics、operations | 逐份核对现行代码、契约、配置及执行命令后更新 |
| knowledge-base 的 README、00_start_here、04_decisions、07_handoff | 更新当前状态、影响边界和接续路线；历史时间线保留 |
| knowledge-base 的 IMAGE_CATALOG、PROTOTYPE_INDEX | 增加真实产品截图入口，区分历史原型与当前实现 |
| 会话/研究/来源索引与综合研究结论 | 作为按日期归档的背景材料保留；本次无新研究来源，不伪造新的研究事实 |
| approved 规格快照、raw 会话、original 研究、原始图片 | 不可变或批准时快照，原文保留；当前解释由正式规格和新状态文档提供 |
| 08_wechat_sources | 外部知识库移交记录按原记录日期保留；未访问或修改外部 Obsidian/DavyBase |
| 99_manifest 的 ARCHIVE_NOTES、READER_TEST | 历史归档与读者测试记录保留；inventory/sha256sums 按当前知识库重新生成 |
| AGENTS.md | 协作和提交规则仍有效，不为文档改写改变用户要求 |

当前界面证据在[截图说明](assets/screenshots/README.md)，本次验证在[文档更新记录](implementation/2026-09-04-documentation-refresh.md)。文档全量整理是统一现状与阅读路径，不是覆写历史或把全部计划标为完成。
