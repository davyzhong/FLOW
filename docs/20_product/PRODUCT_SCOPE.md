---
doc_id: FLOW-PROD-SCOPE-001
title: 产品范围
doc_type: product
status: canonical
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
decision_refs: [D045, D046, D049, D039]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: product
supersedes: []
superseded_by: null
---

# 产品范围

## 含

1. **财务分析轨（当前主体）**：来源登记与财报抽取（B01–B05）、事实合同与勾稽、指标库（v1.1，64 条）、客观快照与冻结、四表一注阅读、四问工作台、报告中心（多格式发布）、Copilot（约束回答）。
2. **经营分析轨（并行第二轨）**：共享数据接入/中间层/指标语义/证据机制，区别仅在数据定义；经营指标目录（O2，43 指标/6 域）、六主题经营快照与 /operations 概览（O4 done）、多格式发布（O3 done）。
3. **横切**：单用户认证与会话、对象存储与发布登记、结构化日志（U8-C）、CI 十六门禁。

## 不含（PRODUCT_BOUNDARIES 的范围侧摘要）

总账系统、自动因果结论、伪造缺失事实、摊月造假、企业多租户/SSO、把数学分解当业务归因。

## 冲突与裁决矩阵（M3.1 Step 1）

| 议题 | 决策链 | 裁决 |
|---|---|---|
| 单角色 or 双受众 | D010（单角色）→ D045（取代） | 双受众、双工作区 |
| 经营分析是未来 or 并行 | D039（未来）→ D045（修订为并行二轨） | 并行第二轨，主观能力后置 |
| 先内部 or 先公开 | D049（公开先行，内部为主场景另试点） | 公开阶段交付，内部独立试点 |
| 推荐策略 | D047（默认推荐策略，保留） | 知识默认推荐，人工评审替代（见知识治理） |
| 名称 | D044 | 保持 FLOW |

无未裁决冲突；历史决定的取代关系以上表为准，单项文件见 [decisions/](../10_governance/decisions/)。
