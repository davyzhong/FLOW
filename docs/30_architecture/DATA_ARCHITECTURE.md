---
doc_id: FLOW-ARCH-DATA-001
title: 数据架构
doc_type: architecture
status: approved
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
decision_refs: [D006, D049]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: data
supersedes: []
superseded_by: null
---

# 数据架构（聚合视图）

- **L1–L4 数据层**（operations methodology）：L1 公开披露 / L2 过程事实 / L3 事件事实 / L4 行动事实；经营轨月度模型不喂年度公开数据（摊月=造假）。
- **来源→事实→快照链**：来源登记（SHA-256）→ 适配抽取 → 归一化 → 勾稽 → 冻结快照（客观）→ 发布登记（PublicationAttempt）。合同见 [financial-facts-contract](../superpowers/specs/financial-facts-contract.md)（原位）与 [flow-v1](../data-contract/flow-v1.md)（原位，机器消费）。
- **指标层**：字典 YAML（版本化）→ DB 激活 → 执行绑定；known_gaps/categories 全量保留（2026-09-08 修复轮）。
- **数据集 YAML（机器消费，原位）**：`synthesis/指标库初始数据集_v0_草案.yaml`、`synthesis/会计基础数据集_v0_草案.yaml`。
