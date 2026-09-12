# FLOW Agent 起点｜2026-09-12

状态：当前接续入口。不要从历史 Phase 或研究材料直接开始实施。

## 最短阅读路径

1. [当前项目状态](PROJECT_STATE.md)：基线、已实现、未验收、在途改动。
2. [D049 正式方向](../../superpowers/specs/2026-09-06-objective-financial-analysis-direction.md)与[事实合同](../../superpowers/specs/financial-facts-contract.md)。
3. [决策日志](../04_decisions/DECISION_LOG.md)与[影响图](../04_decisions/CHANGE_IMPACT_MAP.md)。
4. [下一阶段统一计划](../../superpowers/plans/2026-09-07-unified-next-plan.md)：唯一 U 队列；旧 P/A–H 文档只作历史任务细节与证据。
5. [参考订正总册](../02_research/synthesis/2026-09-07-reference-and-improvement-master.md)与[文档适用性登记](../../documentation-status.md)。
6. [财经分析知识地图](../02_research/2026-09-11-finance-knowledge-map.md)与[Obsidian 内部知识库扫描评估](../02_research/synthesis/2026-09-12-obsidian-internal-kb-assessment.md)：**每次做计划、做功能、做更新前，以 Obsidian vault（本地 `/Users/qiming/ObsidianWiki/`）为内部知识来源**，默认引用 `obsidian-2026-09-12T15:46+08:00`，再按 K1–K8 与统一计划 KG-1–KG-5 取用；只有用户明确要求或单独维护时才建新截面并读取增量。

## 项目定位

FLOW 建设可追溯、确定性、可复核的财务分析工作台。当前从公开财报交付客观分析，内部企业数据另行授权试点；既有物流 Excel 窄切片继续复用，经营轨保留定义和只读演示。当前不是总账、自动因果判断或自动经营决策系统。

## 不可绕过的原则

- 原始文件、原始值、批准快照和冻结报告不能覆盖；更正形成新版本。
- 数据接入、标准事实、指标计算、图表投影和报告输出分层；显示层和 AI 不另算财务数字。
- 主体、期间、币种、合并范围、粒度、口径及来源身份必须一致；缺失不等于零。
- 事实、数学拆解、关联信号、假设与因果分别标记；无量价数据不生成量价桥。
- 旧 Finding 报告保留证据审批；客观报告独立资格已由 U5 建成，后续继续保持其确定性门禁，不擅自放松。
- 单用户认证不等于企业角色权限；公开财报验收不等于内部业务或生产部署验收。
- D047 默认推荐、D048 数据库版本权威/YAML 兼容、D049 客观优先共同有效；不重启逐项 v0 审批。

## 接续动作

先读取 git 状态、已提交实现、最新 CI 和未提交文件，确认当前请求是否授权实施，再完成 D051 Knowledge Gate。当前先做 U8 运行保障；U4 等独立 oracle；U9/O5 等内部数据授权；U10 基于证据决定 V1.1。已完成的 U1–U3、U5–U7、O1–O4 不重建。

每项变更遵循根目录 AGENTS.md：保护用户文件和不可变档案；必要验证后更新相关文档与清单，只提交本任务文件并推送 origin。若仅要求 review 或计划，不实施程序改造。
