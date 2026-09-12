---
doc_id: FLOW-PROD-CAPMAP-001
title: 能力地图
doc_type: product
status: canonical
version: 1.1
created_at: 2026-09-12
updated_at: 2026-09-13
owner: FLOW
decision_refs: [D049, D052, D053, D054]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: product
supersedes: []
superseded_by: null
---

# 能力地图（四态区分：implemented / designed / external-dependency / out-of-scope）

## implemented（已实现，有提交与测试证据）

| 能力 | 归属（三层两模块） | 证据锚点 |
|---|---|---|
| 物流窄切片全链（工作台/调查/Copilot/冻结报告） | 共享分析底座 | Phase 1–10 验收记录 |
| 来源登记与财报抽取/归一/勾稽/复核 | 共享分析底座 + 公开财报模块 | B01–B05；statements 74 测试 |
| 指标库 v1.1（64 指标/167 科目/48 准则/32 分录） | 可见专业治理底座 | 3d4f92d；C01–C06 治理 |
| 客观快照与统一冻结、四表阅读 | 共享分析底座 | U5/U6；迁移头 0024 |
| 经营事实严格期间 + 六主题快照 + 多格式发布 | 共享分析底座 | O2/O3/O4；PublicationAttempt |
| 四问工作台与可解释交互 | 共享分析底座 | U7 |
| 对象存储/发布登记/下载校验 | 共享分析底座 | S3 修复 + O3 typed 409 |
| 结构化日志（JSON 行/旅程关联/敏感遮蔽） | 共享分析底座 | U8-C（088977b） |
| 静态知识库与文档治理体系 | 可见专业治理底座 | flow-knowledge-2026-09-12.1 |

## designed（目标态，未实现；D052/D053 定义）

- 企业内部分析工作台：持续企业分析空间、月度分析周期、Finance BP 轻量提交入口、企业配置与历史学习、双版本报告（专业版 + 管理层版）
- AI 报告生产链：分析型 AI → CFO 角色 AI → 经分专员终审（D054）
- 可见专业治理：规则来源/版本/使用位置的外显查看与企业级配置版本化
- 公开财报模块 C 级出口：多级公开证据分级、自动 Finding、双 AI 角色、例外终审
- actual_vs_budget 预算比较（需内部版本事实；FIN-COMPARE 转换链示例）
- 多维盈利守恒、窄主题分析包、一报一会闭环（原 U9/O5 范围，U8 后按 D053 重新裁决）
- 独立全行 oracle 验证（U4，待外部到料）

## external-dependency

- PDF 渲染依赖部署环境固定 Chromium；MinIO 对象存储（Quay 镜像）；GitHub Actions CI；合规企业云模型 API（待选型）。

## out-of-scope

总账/记账系统、BI 看板化、AI 写作工具、行动任务管理（首版核心外）、企业多租户 SaaS/计费/SSO、自动因果、市场/投资分析、通用 NLP 平台。
