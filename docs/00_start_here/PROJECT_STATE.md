---
doc_id: FLOW-STATE-001
title: PROJECT_STATE
doc_type: state
status: current
version: 4.7
created_at: 2026-09-12
updated_at: 2026-09-26
owner: FLOW
applies_to: repository
---

# FLOW 当前项目状态（唯一 current state）

2026-09-26 更新：大麦常驻库曾在备份后幂等恢复并通过 verify 19/19 两次；随后根 checkout 的旧 `make test-dashboard` 误向常驻 `flow` 附加测试批次 `01a0dcdd-8245-7c17-99aa-fce91a8a7a57`（1 import、12 snapshots、1 run、50,400 metric values），可能成为 API `latest`。只读检查确认未删除/覆盖原大麦批次；未获授权，不回滚、不删除。此前备份 `work/backups/flow-pre-demo-rehydrate-20260926.dump`（SHA-256 `b374a16e…9782d`）早于该新增批次，不能作为当前恢复点。`649a2aba` 已推送并通过 CI run `36232029817`：维度表只展示当前快照事实并显示覆盖分母，完整筛选目录保留；Web 136/136、typecheck、隔离 verify19/19、E2E9/9通过。状态/证据文档提交 `7229cd0d` 与 `4c55f10e` 的 CI 也通过。常驻库页面状态需获批处置后重新只读核验；其他全站矩阵仍未完成。
2026-09-26 补充：API 路由审查发现客观报表快照与经营报告渲染的若干 GET 可能新增冻结快照；这些路由已明确排除在只读探测之外，纳入单独 API 语义评审，不以请求验证其状态。其余 Gate 1 只读矩阵与页面状态验收继续推进。

截至本次文档同步，批次历史 clean-SHA 隔离验收通过（seed/verify19/19、浏览器9/9）；dashboard CI URL冲突已修复，最新SHA/CI见路线图。常驻开发库安全恢复与验证19/19两次完成。大麦发行财报各51行、FY2025覆盖37/40、FY2026 40/40；常驻API有8卡、12/12趋势及2条findings，状态degraded且矩阵保留合理缺格；3000端口 hydration 与KPI缺失原因展示已修复。经营分析点余额读取与派生指标依赖缺陷已修复（FY2026七项运营效率指标均可算，其中流动比率0.8119、资产负债率0.8986、DSO 116.3881天），比率单位和公开披露缺项/内部授权原因按语义显示。40次GET、36个不同路由/参数组合全部HTTP200；正式报告产物历史为空与API持久化一致。其他页面金额/数量格式、Gate1完整视口/错误态复测、批次三与其余页面下钻仍待完成。主线只在`main`串行推进。

上段中的“两次 dashboard CI 失败”及“CI现需修正”仅记录本次修复前状态；以本页顶部更新为准：dashboard job 已通过，完整 workflow 尚在运行。

历史状态快照：下文部分 S01/R0–R4 描述记录了各自交付时的上下文；若与当前状态、分支集成或门禁冲突，以本段和 [CURRENT_ROADMAP](../50_plans/CURRENT_ROADMAP.md) 为准。

**战略方向（2026-09-13 已批准）**：D052–D054 + 经三轮独立规格审查通过的[战略重构设计 V1.1](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)生效——企业内部月度财务经营分析工作台为最终产品，公开财报为独立模块（三层两模块）；固定原则见 [PRODUCT_PRINCIPLES](../20_product/PRODUCT_PRINCIPLES.md)。U8 冻结后先完成 Financial Facts Contract V2、安全/权限子规格和模块边界门禁，旧 U9/U10 不自动续跑。

## 当前执行入口

- **[CURRENT_ROADMAP.md](../50_plans/CURRENT_ROADMAP.md)**（唯一主线：状态真相 + 执行队列）：U08、S01、前端一致性整改与大麦完整财年演示数据 completed（含常驻库装载 G2）；全站深链批次一、二本地完成、批次三待办；C级交叉评已完成但归因、订正和新留出未完成；其余执行顺序见路线图。
- 旧统一计划、O 系列计划、EXECUTION_TODO 与 2026-09-24/25 三份总计划均已 superseded/archived（保留历史细节与证据，不再作为执行依据）
- 文档迁移：[迁移实施计划 M0–M6](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) 已全部关闭（bfc1271 / e373e25，用户确认 2026-09-13）

## 进行中 / 阻塞 / 待授权

1. **U8（已完成并冻结）**：[生产冻结交付记录](../60_delivery/2026-09-13-u8-production-freeze.md)；可恢复基线 `u8-final-baseline`；严格冻结标签 `flow-u8-freeze-20260913`。
2. **U4（blocked）**：旧样本首跑 199 行均不可比较；小米 2026H1 与阿里 FY2027Q1 新 holdout 已冻结并录入独立 oracle，先修版式适配并回归旧样本，再按盲测纪律运行新留出。
3. **[S01 战略边界、事实合同与安全门禁](../50_plans/work_items/S01--post-u8-boundary-contract-security.md)（completed）**：Task 1–5 + R0/R1（台账 §6）+ R2/R3/R4（台账 §7）全部交付，Task 6 正式关闭。阶段 3 起转入[公开模块 C 级出口](../50_plans/work_items/PUBLIC--c-level-exit-protocol.md)（T09–T12，gated）。
4. **公开模块 C 级出口（门禁后）**：执行冻结样本、company-level holdout、可复算/可追源和独立盲评量化协议。
5. **内部工作台与真实企业验证（C 级出口后）**：需内部数据授权；至少连续三个完整月度周期，与同输入人工基准逐周期比较。
6. **旧 U9/O5、U10（待重新裁决）**：仅保留历史工作包身份，不按旧依赖链自动领取。
7. **大麦完整财年演示数据（底座 completed；页面覆盖部分完成）**：24个月synthetic全链已落地；常驻开发库受控恢复、verify19/19两次通过。Dashboard API 200、8卡、趋势12/12、2条findings，仍degraded；财报2份、发布快照1、冻结候选12，静态覆盖FY2025 37/40、FY2026 40/40。毛利矩阵实际/预算比较各10/32格可用，缺格不补零。常驻只读页面显示批次/Finding/财报/经营快照，未发布比较值显式标记；经营分析资产负债表点余额角色问题修复，百分比/倍数/天数已单位化显示。正式报告产物历史为空，其他页面金额/数量格式审计仍待完成。隔离栈verify19/19、浏览器E2E9/9；FY2025四问API500已修复。Gate 1全路由响应矩阵、Gate3/4其他页面呈现/下钻及深链批次三未完成。详见[Gate 1/Gate 2记录](../60_delivery/verification/2026-09-26--damai-visibility-gate1-v1.md)和[剩余体验收口工作包](../50_plans/work_items/UX--post-damai-experience-closeout.md)。合成数据不解除公开C级或真实企业门禁。
8. **第二代静态知识刷新（active）**：批准规格与 preflight 已完成；K0–K6 尚待执行，用户战略裁决前不得切换 `CURRENT_RELEASE`。

## 知识基线

静态知识基线 `flow-knowledge-2026-09-12.1`（D051）；M2 发布 `flow-knowledge-2026-09-12.1` 前，产品设计引用一律使用该前缀。日常执行不读取动态 Obsidian。仓库内不可移动/重写区：五个不可变根（`00_governance/immutable-paths.lock.tsv` 逐文件锁定）、`docs/implementation/p5/` 机器数据路径、`08_wechat_sources/` 档案。

## 能力矩阵与历史证据

已实现能力（物流窄切片、来源与财务事实 B01–B05、指标库 v1.1、报告中心、认证等）与历史验收细节见[历史状态快照](../knowledge-base/00_start_here/2026-09-07-project-state-history.md)与 [HANDOFF](../knowledge-base/07_handoff/)；本页只维护当前事实。

## 更新纪律

每次只依据提交、测试和用户确认更新；修改正式合同先查决策与影响图；实施需对应任务授权。历史段落不叠加到本页。
