---
doc_id: FLOW-STATE-001
title: PROJECT_STATE
doc_type: state
status: current
version: 3.7
created_at: 2026-09-12
updated_at: 2026-09-26
owner: FLOW
applies_to: repository
---

# FLOW 当前项目状态（唯一 current state）

2026-09-26 更新：CI dashboard 数据库 URL 冲突已修复；隔离大麦旅程 verify19/19、浏览器E2E9/9；深链批次一、二 API/安全51/51、Web单测133/133、深链E2E15/15、typecheck/合同/M6通过，提交 `7976691` 及后续验收提交均已推送，CI状态见路线图。对当前常驻开发 API 的只读核验发现：dashboard 404 `dashboard_not_ready`、internal batch 0、findings 0、publishing snapshots 0、freeze candidates 0；但财报2、公开经营期间7、大麦覆盖FY2025 37/40与FY2026 40/40、经营快照2仍在。故 G2 既往验收不代表当前开发库仍有数据；已将受控恢复（先全量备份、幂等seed、不清库/不迁移、seed后验证）列为下一步，尚未执行写入。Gate 1全路由覆盖矩阵仍未完成、深链批次三未开始。此前关于两次 CI 失败的描述记录的是历史状态。

截至 2026-09-26，远端 `main` 最新已推送提交为 `59b328dc`。批次历史功能在干净 SHA `59b328dc` 的隔离 Damai 全旅程复验通过（seed/verify 19/19、浏览器9/9）；但 GitHub Actions runs `36222136591`（`430020f`）和 `36222489952`（`59b328dc`）的 dashboard job 均因 CI 注入 `DATABASE_URL=/flow` 与 `flow_test` 安全守卫冲突而失败，其他 jobs 仍运行中。U8、S01、前端一致性 Task 0–9、大麦完整财年数据包均已完成；常驻库大麦装载 G2 曾于 2026-09-25 按计划完成并 verify 19/19，但本轮未连接或写入常驻 `flow`，当前行数/页面数据量未复核。测试库隔离于 `b60c51b` 修复；小米 2026H1 与阿里 FY2027Q1 holdout 已冻结并录入独立 oracle（`926af825`）。公开 C 级交叉评42项已确认异常为抽取错误；109项口径疑点待裁决，京东物流200格英文原件待重核，抽取修订和新留出盲测未完成。大麦静态数据合同有24个月经营明细（1,920实际、10,752预算、4,800应收回款、768财务实际，含合计守恒 OCF）；发行财报每份51行，静态覆盖 FY2025 37/40、FY2026 40/40。隔离验收中 OCF KPI可用、趋势12/12；毛利矩阵实际/预算比较各10/32格，缺格保持 unavailable、不补零。`make test-dashboard` 已限制为本机 `flow_test`，本地拒绝写常驻 `flow` 的守卫有效；CI现需修正通用 URL 注入与安全测试配置冲突。Gate 1首轮仍绑定 `main@3ff95115` + overlay `1ede2648…`，完整 Gate 1全路由复测及 Gate 3–5其余页面呈现/下钻仍待完成。当前批次历史入口不等于其他经营/财务页面缺数均已解决。主线只在 `main` 串行推进。

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
7. **大麦完整财年演示数据（底座 completed；页面覆盖部分完成）**：24个月 synthetic 全链已落地，静态财务实际768条，含守恒分摊的 OCF；G2常驻库装载于2026-09-25曾验收19/19，本轮未对常驻库执行读写核对或数据操作。隔离栈 verify 19/19、浏览器八页面/旅程 E2E 9/9；OCF KPI可用、趋势12/12。财报每份51行，指标覆盖 FY2025 37/40、FY2026 40/40。毛利矩阵实际与预算比较各10/32格可用，缺格保持 unavailable、不补零，整体 degraded。FY2025四问API 500已修复。Gate 4 `/data` 批次历史列表本轮实现并在本地通过API/UI/合同与文档门禁，CI待验；此项仅提供批次历史索引，不等于其余经营/财务页面已全部补齐。证据见[Gate 1/Gate 2记录](../60_delivery/verification/2026-09-26--damai-visibility-gate1-v1.md)和[剩余体验收口工作包](../50_plans/work_items/UX--post-damai-experience-closeout.md)。合成数据不解除公开 C 级或真实企业门禁。
8. **第二代静态知识刷新（active）**：批准规格与 preflight 已完成；K0–K6 尚待执行，用户战略裁决前不得切换 `CURRENT_RELEASE`。

## 知识基线

静态知识基线 `flow-knowledge-2026-09-12.1`（D051）；M2 发布 `flow-knowledge-2026-09-12.1` 前，产品设计引用一律使用该前缀。日常执行不读取动态 Obsidian。仓库内不可移动/重写区：五个不可变根（`00_governance/immutable-paths.lock.tsv` 逐文件锁定）、`docs/implementation/p5/` 机器数据路径、`08_wechat_sources/` 档案。

## 能力矩阵与历史证据

已实现能力（物流窄切片、来源与财务事实 B01–B05、指标库 v1.1、报告中心、认证等）与历史验收细节见[历史状态快照](../knowledge-base/00_start_here/2026-09-07-project-state-history.md)与 [HANDOFF](../knowledge-base/07_handoff/)；本页只维护当前事实。

## 更新纪律

每次只依据提交、测试和用户确认更新；修改正式合同先查决策与影响图；实施需对应任务授权。历史段落不叠加到本页。
