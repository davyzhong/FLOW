---
doc_id: FLOW-WI-U04
title: U04 独立 oracle 录入与全行验证
doc_type: work-item
status: active
version: 1.3
created_at: 2026-09-12
updated_at: 2026-09-29
owner: FLOW
depends_on: [FLOW-SPEC-V1-DESIGN-001]
acceptance_refs: [U4-fullrow-diff, U4-holdout-generalization]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: verification
supersedes: []
superseded_by: null
---

# U04 独立 oracle

- **范围**：由未参与抽取器开发的独立会话录入 oracle；全行 diff 与留出泛化验收。
- **当前执行步骤（2026-09-29）**：已按 TDD 修复顺丰“合并及公司”文本型报表、腾讯动态定位财务报表、以及中通公告重复字形文本层解析；修复 holdout comparator 的列值提取与报表范围消歧；运行器默认只跑已降级旧三样本，新留出须显式 `--samples` 指定。旧回归 run `2026-09-29-adapter-v4` 为顺丰137/137、腾讯32/32、中通30/30，共199/199匹配、0错配、0不可比较；这只是历史样本回归，不是新的盲留出通过。首个提交 `07819d56` 的本地解析/脚本门禁通过但 GitHub smoke 因生产镜像缺少 `pypdf` 失败；根因是该包误列在 dev 组，现已移至运行依赖并更新 `uv.lock`。修复后的隔离 Compose 项目 `flowu04smoke` 中 API/Web 健康、迁移与 dev principal seed 成功；修复提交的准确 SHA CI 尚待验证，因此实现仍未冻结。**目前未读取/检查小米与阿里抽取结果；只有修复提交 CI 绿后才做两样本首次未调参运行。**
- **独立 oracle 审计**：冻结的14份 C 级报告目前没有完整逐行独立 oracle（0/14）。5份已登记 oracle 对应另外的 holdout，均属部分行转录。不得将 L1 v5、实现方复核或既有 AI 交叉评冒充完整独立 oracle。
- **首跑历史与降级纪律**：2026-09-24 三份旧候选共199行均 `not_comparable`，不是准确率通过或数值失败；解析修复后可作为回归。小米与阿里新留出在首次机器运行前不得用于版式适配、参数选择或人工纠错。发现样本已被实现用于调参时，按 `oracle-register.md` 降级并启用已冻结备选，不重新抽签。
- **验收**：全行 diff 通过率报告 + 留出集泛化结论；差异逐项归因（口径/抽取/数据三类）。当前旧三样本回归产物见 `validation/financial_reports/holdout_runs/2026-09-29-adapter-v4/`；生产依赖 smoke 已在隔离 Compose 实测修复；新的小米/阿里结果仍待修复提交准确 SHA CI 绿后首次运行。
- **禁止**：为通过 diff 调整 oracle；用公开数据倒造内部行。
