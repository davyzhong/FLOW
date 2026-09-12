---
doc_id: FLOW-PMAP-001
title: FLOW 产品知识映射 v1.0
doc_type: product-mapping
status: canonical
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: flow-knowledge-2026-09-12.1
source_refs: [GRP-A-finance, GRP-W1-wechat, GRP-D-wiki]
authority_level: D
sensitivity: public
effective_from: 2026-09-12
supersedes: []
superseded_by: null
---

# FLOW 产品知识映射 v1.0

| 知识 | FLOW 对象 | 当前能力 | 数据层 | 采用状态 | 缺口/风险 | 规格/任务 |
|---|---|---|---|---|---|---|
| FIN-STAT-001 勾稽 | B 系列勾稽器 + 发布门禁 | 已实现（缺表守卫） | L1 | 采用 | 独立全行验证待 U4 | financial-facts-contract |
| FIN-QUAL-001 净现比 | 指标库 + 客观报告 | 已实现（含负分母政策） | L1 | 采用 | — | metrics |
| FIN-DUPONT-001 杜邦 | 客观报告叙事候选 | 未实现 | L1 | 试点候选 | 报告章节合同未定 | U5 后续 |
| FIN-EBITDA-001 三口径 | 指标库口径字段候选 | 部分（分部 YAML） | L1 | 后置 | 口径变体 schema 未定 | metrics v1.2 |
| FIN-RECV-001 DSO | O2 经营指标候选 | 部分（43 指标含回款类） | L1/L2 | 试点候选 | 账龄属 L2 待授权 | O2/O5 |
| METHOD-QA-001 四问 | 四问工作台 | 已实现（U7） | L1+ | 采用 | 方法层语料扩充中 | copilot |
| METHOD-REPORT-001 四列表 | 报告中心 + /operations | 已实现（O3 多格式） | L1/L2 | 采用 | 状态灯阈值版本化待深化 | operations |
| OPS-PROFIT-001 单票拆解 | O5 窄主题分析包候选 | 未实现 | L2/L3 | 后置 | 硬依赖 U9/O5 授权 | U9/O5 |
| OPS-CFO-001 红黄绿灯 | /operations 概览 | 部分 | L1/L2 | 试点候选 | 阈值配置界面 | operations |
| OPS-CPP-001 ABC 分摊 | 分部核算底座范本 | 未实现 | L3 | 后置 | 授权 + 分摊引擎 | U9 |
| OPS-LOGI-001 物流科目 | 经营成本指标 YAML 候选 | 部分（43 指标） | L1/L2 | 试点候选 | 逐项核验公式/授权 | O2 |
| OPS-MASTER-001 主数据 | U9 主数据与版本合同 | 未实现 | L2 | 后置 | 授权 + schema | U9 |
| GOV-METRIC-001 全要素 | C 系列指标治理 | 已实现（C01–C06） | 横切 | 采用 | 目标值管理部分 | metrics |
| GOV-AUTH-001 授权边界 | U9/O5 门禁 | 已实现（流程约束） | 横切 | 采用 | — | D051/U9 |
| TECH-COPILOT-001 推断分离 | Copilot 评测 + 四问 | 已实现 | 横切 | 采用 | few-shot 语料核验 | copilot |

规则变更：任何「后置→采用/试点」跃迁改变产品范围/合同/优先级时，须经正式决策（D 流程）后进入规格。
