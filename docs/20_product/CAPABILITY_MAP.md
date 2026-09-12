---
doc_id: FLOW-PROD-CAPMAP-001
title: 能力地图
doc_type: product
status: canonical
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
decision_refs: [D049]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: product
supersedes: []
superseded_by: null
---

# 能力地图（四态区分：implemented / designed / external-dependency / out-of-scope）

## implemented（已实现，有提交与测试证据）

| 能力 | 证据锚点 |
|---|---|
| 物流窄切片全链（工作台/调查/Copilot/冻结报告） | Phase 1–10 验收记录 |
| 来源登记与财报抽取/归一/勾稽/复核 | B01–B05；statements 74 测试 |
| 指标库 v1.1（64 指标/167 科目/48 准则/32 分录） | 3d4f92d；C01–C06 治理 |
| 客观快照与统一冻结、四表阅读 | U5/U6；迁移头 0024 |
| 经营事实严格期间 + 六主题快照 + 多格式发布 | O2/O3/O4；PublicationAttempt |
| 四问工作台与可解释交互 | U7 |
| 对象存储/发布登记/下载校验 | S3 修复 + O3 typed 409 |
| 结构化日志（JSON 行/旅程关联/敏感遮蔽） | U8-C（088977b） |
| 静态知识库与文档治理体系 | flow-knowledge-2026-09-12.1 |

## designed（已设计未实现）

- actual_vs_budget 预算比较（需内部版本事实；FIN-COMPARE 转换链示例）
- 多维盈利守恒、窄主题分析包、一报一会闭环（U9/O5 范围）
- 独立全行 oracle 验证（U4，待外部到料）

## external-dependency

- PDF 渲染依赖部署环境固定 Chromium；MinIO 对象存储（Quay 镜像）；GitHub Actions CI。

## out-of-scope

总账、多租户/SSO、自动因果、市场/投资分析、通用 NLP 平台。
