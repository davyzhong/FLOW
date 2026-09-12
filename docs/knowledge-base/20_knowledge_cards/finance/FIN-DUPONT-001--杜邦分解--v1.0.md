---
doc_id: FIN-DUPONT-001
title: 杜邦分解
doc_type: knowledge-card
status: verified
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: pre-static-obsidian-2026-09-12T15:46+08:00
source_refs: [GRP-A-finance, GRP-D-wiki]
authority_level: D
sensitivity: public
domain: financial_analysis
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [FIN-MARGIN-001]
related_code: []
---

# 杜邦分解

- **定义**：ROE = 净利率 × 总资产周转率 × 权益乘数 的三层分解。
- **业务目的**：把股东回报拆成盈利、效率、杠杆三驱动，定位回报变化的来源。
- **输入**：净利润、收入、总资产（期初期末均值）、净资产（均值）。
- **规则**：资产/权益用期初期末平均；三因子连乘须与直接计算的 ROE 勾稽；杠杆因子用平均权益而非期末。
- **适用**：年度/半年度口径的趋势与对标。
- **不适用**：权益剧烈变动期（均值失真）；季度年化（须显式年化假设）。
- **常见误用**：期末值代替均值；把权益乘数上升当「改善」（杠杆是双刃指标）。
- **来源与核验**：A 组《杜邦分析法-拆解企业盈利能力的财务显微镜》；wiki 驾驶舱簇的四层看板结构含杜邦穿透路径。
- **FLOW 影响**：客观报告叙事骨架候选；dashboard 穿透路径设计参照。
