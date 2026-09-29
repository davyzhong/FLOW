---
doc_id: FLOW-WI-U04
title: U04 独立 oracle 录入与全行验证
doc_type: work-item
status: active
version: 1.5
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
- **U4 阶段关单（2026-09-29 深夜）**：工作包范围内交付全部完成。①旧三样本回归两次全绿（adapter-v4/v5 各 199/199、0 错配、0 不可比）；②小米/阿里未调参首跑如实登记失败后，按 §4.5 用样本开发 `hk_interim_english`/`hk_quarterly_highlights` 两适配器并降级为回归集，适配后回归小米 24/25+2 勾稽、阿里 15/15+2 勾稽（唯一 not_comparable 为 Term bank deposits 真实重名行，比较器多候选不猜从严属设计），旧样本零退化；③备选候选 yunda/jdl 按顺位启用并先冻结+oracle（§1a 顺序保持）后首跑：yunda 0/20（A 股适配器列绑定错位+「3、合并利润表」编号标题缺口）、jdl 0/25（UnsupportedLayoutError 显式降级），失败原始保留、两样本保持留出身份；④泛化缺口（韵达 A 股版式、京东物流英文中报版式）已登记为第 5 项 C 级 Go/No-Go 裁决输入。oracle 修订史（值零变更）见各 oracle 文件头与 manifest previous_claim。TDD：`tests/statements/test_extraction_adapters.py` 19/19。
- **独立 oracle 审计**：冻结的14份 C 级报告目前没有完整逐行独立 oracle（0/14）。5份已登记 oracle 对应另外的 holdout，均属部分行转录。不得将 L1 v5、实现方复核或既有 AI 交叉评冒充完整独立 oracle。
- **首跑历史与降级纪律**：2026-09-24 三份旧候选共199行均 `not_comparable`，不是准确率通过或数值失败；解析修复后可作为回归。小米与阿里新留出在首次机器运行前不得用于版式适配、参数选择或人工纠错。发现样本已被实现用于调参时，按 `oracle-register.md` 降级并启用已冻结备选，不重新抽签。
- **验收**：全行 diff 通过率报告 + 留出集泛化结论；差异逐项归因（口径/抽取/数据三类）。当前旧三样本回归产物见 `validation/financial_reports/holdout_runs/2026-09-29-adapter-v4/`；生产依赖 smoke 已在隔离 Compose 实测修复；修复提交的功能性 CI 通过，但 CI workflow 收尾清理仍需获批修正；新的小米/阿里结果仍待准确 SHA CI 全绿后首次运行。
- **禁止**：为通过 diff 调整 oracle；用公开数据倒造内部行。
