---
doc_id: FLOW-ARCH-METRIC-001
title: 指标与分析架构
doc_type: architecture
status: approved
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
decision_refs: [D013, D047, D049]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: metrics
supersedes: []
superseded_by: null
---

# 指标与分析架构（聚合视图）

- **指标治理**：草稿→验证→激活→退役生命周期 + 审计 + 影响沙箱（C01–C06）；全要素配置（公式+口径+目标+阈值）版本留痕（GOV-METRIC-001）。
- **执行引擎**：绑定 {item,abs} 映射、sum 算子沙盒、负分母不伪造比率政策、Decimal 全程（不经 float）。
- **分析分层**：事实与计算（客观）→ 证据推断（显式标注）→ 行动建议（四问闭环 METHOD-QA-001）；分析消费冻结快照，不直连业务表。
- **知识源**：指标口径与方法的 canonical 知识在 flow-knowledge-2026-09-12.1（16 卡 + 11 手册）。
