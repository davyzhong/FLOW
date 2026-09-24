---
doc_id: FLOW-REV-DAMAI-PLAN-20260924
title: 大麦物流演示数据实施计划（v2.4）独立评审
doc_type: review
status: open
version: 1.0
created_at: 2026-09-24
updated_at: 2026-09-24
last_reviewed_at: 2026-09-24
owner: FLOW
subject_ref: codex/damai-logistics-implementation@7e252cb
findings: [damai-plan-quality-high, damai-governance-registration-late, damai-gate-ordering-defect, damai-spec-manifest-drift, damai-fault-injection-gap, damai-e2e-acceptance-ambiguity, damai-change-discipline-unwritten]
applies_to: repository
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/superpowers/plans/2026-09-24-damai-logistics-demo-data-implementation-plan.md
  - docs/superpowers/specs/2026-09-24-damai-logistics-demo-data-design.md
  - docs/80_reviews/2026-09-24-damai-demo-partial-implementation-review.md
  - docs/superpowers/plans/2026-09-24-project-baseline-repair-implementation-plan.md
evidence_refs:
  - codex/damai-logistics-implementation@7e252cb
confidentiality: project-internal
---

# 大麦物流演示数据实施计划（v2.4）独立评审

评审对象：`codex/damai-logistics-implementation@7e252cb` 上的实施计划 v2.4、
设计规格 v1.5 与半成品审查报告（三份文档均在 `source_refs`）。

## 1. 总体结论

**计划整体质量高，可以执行；建议在 Task A1 开工前先处理两条排序/治理缺陷（§3 的 P1-1、P1-2），
其余为执行期注意事项。**

计划的优点明确，先予确认：

- 红灯测试先行（A1 明确"不允许先改实现后补断言"），符合本仓库 TDD 纪律；
- 有明确的停机条件（§7）和"明确不做"清单（§0、规格 §2.2），范围护栏完整；
- 半成品审查的 5 个 P0 全部有对应修复任务（A2/A3/A4），完成定义与审查 §5 闭环；
- 数据量级自洽：24×40×2=1,920 经营明细、12×4×4×8×7=10,752 预算、24×40×5=4,800 AR，
  与规格 §3.3 一致；
- 正确识别了"5 个 playbook 不可能产出 6 个系统 Finding"的口径矛盾，
  降级为"≥6 个可追溯信号、≤5 个系统 Finding"，不伪造能力；
- 已核实的疑点均排除：CI `on: push` 无分支过滤，"同一 SHA CI 全绿"在分支上可达；
  依赖的 `FLOW-PLAN-BASELINE-REPAIR-20260924` 真实存在；
  计划列出的文件路径（`fixtures/damai/` 包、`p5_metric_coverage_v1.yaml`、
  `apps/web/e2e/` 基础设施）在分支上均实际存在。

## 2. 评审方法

对照项目治理合同（AGENTS.md、D052–D054、CURRENT_ROADMAP 唯一执行入口纪律）、
文档门禁合同（`scripts/documentation/metadata.py`）与分支实际代码状态逐项核对；
数量级、文件路径、CI 触发条件均经实测验证，非仅凭文档转述。

## 3. 值得优化的点

### P1-1 治理登记被排在最后，应先补一个最小登记

大麦工作在当前 main 与分支的 `CURRENT_ROADMAP.md`、`PROJECT_STATE.md` 中均无登记，
也没有对应 work package；路线图登记被安排在 C3 / baseline-repair Task 2（即全部做完之后）。
按 D053"路线图是唯一执行入口"与本项目此前多 Agent 状态漂移的教训，
权威状态在执行期内长时间与现实脱节正是漂移根因。

**建议**：开工前增加一个最小登记提交——在 CURRENT_ROADMAP 登记大麦工作包（status: active），
或新建 `docs/50_plans/work_items/` 工作项；C3 再按实测结果刷新为完成态。
纯文档、低风险，不占用实施时间。

### P1-2 门禁前置依赖顺序有缺陷

M6 目前在 main 和分支上都是红的（`CODE_OF_CONDUCT.md`、`CONTRIBUTING.md`、`SECURITY.md`
缺 frontmatter，分支上另有 `fixtures/damai/README.md`），已实测确认。
但 baseline-repair Task 1（修复门禁）被排在大麦 C3 才执行，而 A4 的验收要求是
"生成的 README 不得破坏 M6 文档门禁"——门禁本身红着，A4 无法自证"不破坏"。

**建议**：把 baseline-repair Task 1 前置为 A0（A1 之前）。它只改 3 份顶层文档的
frontmatter，几分钟完成，让 A4/C3 的门禁验收有绿色基线可比对。

### P2-1 规格与实现已有小漂移：`manifest.py`

规格 §4.1 约定生成层包含 `manifest.py` 模块，实际 manifest 逻辑（含 XLSX 语义指纹）
在 `scripts/build_damai_demo.py` 中，`fixtures/damai/` 包内没有 `manifest.py`。
计划 A4 按现实改 build 脚本是对的，但 approved 规格与实现不一致正是本计划要消除的
问题类型。建议 A2/A4 顺手修订规格 §4.1，或补一个 `manifest.py` 薄模块对齐规格。

### P2-2 故障注入缺"发布物生成失败"一类

B1 的三类故障注入（不变量、第二份财报、freeze）未覆盖规格 §6 列出的
"对象存储不可用/发布物生成失败"降级路径。建议要么补入注入清单，
要么在 B1 显式写明不覆盖的理由，避免验收口径模糊。

### P2-3 E2E 验收口径未明确

C2 的八页面真实 E2E（compose + Playwright + 页面上传 XLSX）很重，
计划未写明它是否进入 CI required jobs 还是仅本地验收；若 CI 不含 E2E，
C3 的"同一 SHA CI 全绿"与"八页面通过"之间存在缝隙。
另外 C1 的验收证据写入 `work/damai-demo/`（不入 git），CI 上建议以 artifact
形式留存 receipt，否则跨会话无法复核。

### P2-4 "范围变更先改计划"纪律只在会话口头，未写入计划文档

用户已明确"任何范围或验收口径变化都会先更新计划文档并提交推送，再修改代码"，
但计划 §2 约束与 §7 停机条件均未收录这条。后续接手的 Agent 只读文档，
建议补入 §2，使纪律可被发现。

### P3-1 与主线协同关系建议在 C3 写明

大麦发行版可成为 U4 独立 oracle 之外的第二验证数据源、U09 授权内部试点的演示底座。
建议 C3 刷新路线图时把这条协同写明，避免 demo 成为孤立交付物。

### P3-2 跨版本 re-seed 未定义

幂等验收只覆盖"同版本二次 seed 零增长"；发行包 v1→v2 升级后的 re-seed 行为未定义。
可接受为 v1 范围外，但建议写入"明确不做"，防止后续 Agent 误假设。

## 4. 提示（非缺陷）

- 口头/会话内引用的版本与 SHA 易过期：本次用户转述为"计划 v2.3、提交 cb98d65"，
  实际文件已 v2.4、分支 HEAD 为 `7e252cb`。计划 §0 的执行进度表是好机制，
  评审与交接时应一律以分支 HEAD 为准；
- XLSX 语义指纹机制已在 build 脚本中存在（zip 容器非字节确定），A4 复用时
  建议把指纹算法版本记入 manifest，保证验收可复核；
- B3 修改既有 `metric-coverage-section` 组件，不触发新增页面规范
  （无需 AppShell/navigation.spec 新路由），但组件单测与 metric-library 守护测试
  需同步更新，计划已覆盖。

## 5. 建议的执行顺序调整

```text
A0（新增）：baseline-repair Task 1 门禁修复 + roadmap 最小登记
A1 → A2 → A3 → A4（不变）
B1 → B2 → B3（不变；B1 补充发布物失败注入或显式排除说明）
C1 → C2 → C3（不变；C2/C3 明确 E2E 执行位置与证据留存）
```

除 A0 前置外，原计划的 A→B→C 严格串行顺序与任务切分无需变动。
