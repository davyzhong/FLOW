---
doc_id: FLOW-COMPETITIVE-001
title: FLOW 竞品调研 · 路线图与阅读顺序
doc_type: competitive-research
status: current
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
applies_to: competitive-research
---

# FLOW 竞品调研 · 路线图与阅读顺序

> 目的：盘点面向"内部经营分析 / 财报分析 / 财务指标体系 / 杜邦 / 经营快照"的国内外可比产品，沉淀其方法论与系统设计，形成对 FLOW 的改进清单。

## 阅读顺序

| # | 文档 | 类型 | 一句话定位 |
| --- | --- | --- | --- |
| 1 | [open-source-ai-financial.md](open-source-ai-financial.md) | 开源 AI 财分 | 面向二级市场的 AI 财务助手 / 研究平台，盘点最新开源生态 |
| 2 | [commercial-ai-report.md](commercial-ai-report.md) | 商业 AI 财分 | AlphaSense / Hebbia / Hebbia / Tagnos 等头部商业 AI 财分产品 |
| 3 | [open-source-bi.md](open-source-bi.md) | 开源 BI | Superset / Metabase / DataEase 等通用 BI 平台 |
| 4 | [china-financial-bi.md](china-financial-bi.md) | 中国本土 BI / 终端 | FineBI / 帆软 / Wind / iFinD / Choice / 通联数据 等中国市场玩家 |
| 5 | [consulting-frameworks.md](consulting-frameworks.md) | 咨询方法论 | McKinsey / BCG / 长桥 等方法论框架（杜邦、PIMS、Valuation） |
| 6 | [summary-and-positioning.md](summary-and-positioning.md) | 综合 | 5 份调研汇总 + FLOW 在行业里的定位 |
| 7 | [optimization-checklist.md](optimization-checklist.md) | 改进清单 | 30+ 条改进建议，分优先级 / 成本 / 风险 |
| 8 | [2026-09-15-ai-data-layer-mcp-supplement.md](2026-09-15-ai-data-layer-mcp-supplement.md) | 增量补充 | 受治理数据层 + MCP 通道（2026 新动向）与 S-1~S-6 增量条目 |

## 调研范围

- **内部经营分析 / 财报分析 / 财务指标体系**：FLOW 的核心场景
- **公开市场投资研究**：次要场景，仅做参考（因为重点不是二级市场投资）
- **通用 BI 平台**：作为对标 FLOW 在看板 / 仪表盘能力的方向
- **中国本土玩家**：最直接竞争，因为中国会计准则 + 中文报告语境
- **管理咨询方法论**：作为"应该长什么样"的方法背书

## 不在范围

- 通用 ERP / 财务记账（GnuCash / Ledger 等）—— 不解决"分析"问题
- 二级市场投资工具（聚宽 / 米筐 / Backtrader）—— 选股不是 FLOW 的定位
- 个人记账（Money Pro / YNAB）—— 不解决企业内部经营分析

## 调研维度

每份调研文档按以下维度对比：

1. **产品定位**：面向谁、解决什么、不解决什么
2. **数据模型**：财务事实 / 维度 / 指标的组织方式
3. **指标体系**：杜邦 / VAS / NISSIM / 自定义
4. **分析方法**：杜邦 / 趋势 / 对标 / 同业 / 情景 / 敏感性
5. **可视化**：报表 / 图表 / 仪表盘 / PPT / 看板
6. **生成与发布**：MD&A 自动写、报告批量出、PDF/PPTX/HTML
7. **AI 能力**：LLM 接入、自动解读、问数（Q&A）、智能问答
8. **技术栈**：开源语言 / 部署 / 私有化 / 数据安全
9. **商业模式**：订阅 / 一次性 / Freemium / 自建
10. **对 FLOW 的启发**：可借鉴 / 不可借鉴 / 差异化机会

## 调研来源

- 公开搜索（web_search）+ 各产品官方文档 + GitHub README
- 行业研究报告（山东财经大学深圳研究院 2025 财经数据行业报告 等）
- 个人体验 / 演示视频 / 用户评价

**调研截止**：2026-09-15。竞品数据 / 定价 / 功能可能已过时，引用时标注"调研时点"。