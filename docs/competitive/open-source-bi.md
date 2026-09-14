---
doc_id: FLOW-COMPETITIVE-BI-OS
title: 开源 BI 平台 · 调研
doc_type: competitive-research
status: current
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
related: [./README.md, ./summary-and-positioning.md]
---

# 开源 BI 平台

> 调研时点：2026-09-15。覆盖可作为 FLOW 看板 / 仪表盘层借鉴的开源 BI 平台。

## 一、市场观察

BI（Business Intelligence）是 FLOW "看板层" 的对标方向。FLOW 自建的 `apps/web/components/dashboard/` + Dashboard Widget 已是一个轻量 BI 系统，但相比成熟 BI 还欠缺「拖拽式看板 + 跨数据集查询 + 权限管理」。

## 二、Apache Superset (⭐ 60k+)

- **定位**：Airbnb 开源的"企业级数据可视化 + 探索 + 仪表盘平台"
- **核心能力**：
  - SQL Lab：内置 Web IDE，分析师可直接写 SQL 查任何数据库
  - 30+ 可视化组件：柱状图 / 折线图 / 饼图 / 桑基 / 地图 / 透视表
  - 自定义图表插件（deck.gl / ECharts / d3）
  - 行级安全（RLS）+ 角色 + 资源权限
  - 告警 + 调度
- **数据源**：50+ 内置连接器（PostgreSQL / MySQL / ClickHouse / Druid / Snowflake / BigQuery / Athena / 等等）
- **技术栈**：Python (Flask) + React + TypeScript + Apache ECharts / d3
- **部署**：Docker / Helm / K8s
- **商业模式**：纯开源（Apache 2.0），商业支持 Preset.io 卖 SLA
- **对 FLOW 启发**：
  - ① **图表组件丰富度**：FLOW 目前的图表是手写 SVG + 自定义组件，覆盖 6 类；如果要做完整看板需要补充 桑基 / 地图 / 透视表
  - ② **SQL Lab**：FLOW 财务分析师是"业务方"，不会写 SQL。可以做一个「指标查询 → 自动生成 SQL → 可视化」的低代码工具
  - ③ **行级权限**：FLOW 当前是单租户，单企业内多角色。后续如果多企业 / 多子公司，要补 RLS
  - ④ **告警 / 调度**：FLOW 的「指标覆盖率告警」思路值得加

## 三、Metabase (⭐ 38k+)

- **定位**：开源 BI，偏自助式分析（业务方友好）
- **核心能力**：
  - 「问题问数」：用户问「上个月销售怎么样」 → 自动生成图表
  - 拖拽式 dashboard 编辑
  - 内置可视化（柱 / 折线 / 饼 / 区域 / 漏斗 / 趋势）
  - 数据源 20+（PG / MySQL / Snowflake / BigQuery / ClickHouse / MongoDB 等）
  - 邮件 / Slack 订阅与告警
  - 嵌入式（嵌入到其他系统）
- **技术栈**：Clojure + React + Recharts
- **部署**：Docker / JAR 单文件
- **商业模式**：开源 + Metabase Cloud（托管）
- **对 FLOW 启发**：
  - ① **嵌入式**：Metabase 强大的「嵌入到第三方系统」能力值得借鉴——FLOW 的 Widget 概念已经是这个方向，但目前只能在 daimon-canvas 里嵌入。可以扩展为「任意网页嵌入」
  - ② **问数**：和上面 AlphaSense 启发一致，业务方友好的 Q&A 是核心
  - ③ 整体思路 Metabase 比 Superset 更接近 FLOW 的"自助分析 + 友好"定位

## 四、DataEase (⭐ 19k+) — 中国本土

- **定位**：国产开源 BI（FIT2CLOUD 飞致云）
- **核心能力**：
  - 拖拽式看板 + 30+ 图表
  - 数据源：MySQL / PG / Oracle / ClickHouse / Doris / 等等，特别支持国产数据库（达梦 / 人大金仓 / 神通）
  - 国产化适配：信创、麒麟 OS
  - **Excel / 飞书 / 钉钉 / 企微集成**
  - 模板市场（场景化 dashboard 模板）
- **技术栈**：Java (Spring Boot) + Vue + Ant Design
- **部署**：Docker / 单机二进制 / 信创服务器
- **商业模式**：开源 + 商业版（DataEase Enterprise，订阅 / 买断）
- **对 FLOW 启发**：
  - ① **国产化适配**：是中国客户刚需，FLOW 的多租户化部署可以参考
  - ② **场景化模板**：DataEase 提供「行业 dashboard 模板市场」。FLOW 可以做「行业指标体系模板 + 看板模板」，比如「物流行业财务分析 dashboard 模板」
  - ③ **飞书 / 企微集成**：FLOW 当前没做集成，可以加 "飞书机器人推送指标快照"

## 五、Apache ECharts (⭐ 60k+) / AntV (⭐ 32k+)

- **定位**：纯可视化库，不是 BI 平台。但所有 BI 都基于它们
- **ECharts**：百度系，柱 / 折线 / 饼 / 桑基 / 树图 / 雷达 / 地图全覆盖；中国市场占率最高
- **AntV**：蚂蚁系，G2Plot + G6 + L7；偏学术 / 设计师友好
- **对 FLOW 启发**：
  - ① FLOW 当前用原生 SVG 自绘图表。直接换 ECharts / G2Plot 可减少 70% 维护成本，并解锁更多图表类型
  - ② 静态站 `docs/library/index.html` 改用 ECharts 渲染图表（避免 SVG 自绘）能减少 300+ 行代码

## 六、其他值得关注

- **Redash** (⭐ 26k)：轻量查询 + 仪表盘，偏 SQL 工作流
- **Knime / Orange**：拖拽式数据分析，机器学习流程化
- **Cube.js** (⭐ 16k)：API 层 BI，metric layer（与 FLOW 的指标字典思路一致）
- **dbt** (⭐ 11k)：数据建模 + 文档 + 测试，模式与 FLOW 的「指标版本化」有共鸣

## 七、横向对比

| 产品 | 易用性 | 可视化丰富度 | AI | 中文支持 | 私有化 | 推荐场景 |
| --- | --- | --- | --- | --- | --- | --- |
| Superset | 中（SQL） | 极高 | 无 | 弱 | 是 | 大企业 |
| Metabase | 高 | 中高 | 部分（Q&A） | 弱 | 是 | 中小企业 |
| DataEase | 高 | 中高 | 无 | 强 | 是 | 中国信创 |
| Redash | 高 | 中 | 无 | 弱 | 是 | 团队内部查询 |
| ECharts | — | 极高 | — | 强 | 是 | 图表库 |
| Cube.js | 中（API） | 高（前端） | 无 | 中 | 是 | 指标 API |

## 八、对 FLOW 的核心启发

1. **看板 / 仪表盘层是 FLOW 必须继续投入的方向**：当前只有 Widget + 静态 HTML。应该补：
   - **拖拽式 dashboard 编辑器**（学习 DataEase）
   - **更多图表类型**：桑基 / 地图 / 漏斗 / 雷达
   - **跨数据集查询**：从单报表查询 → 跨公司跨期间
2. **指标层抽象（cube.js / dbt 模式）**：cube.js 的 metric layer（指标 → SQL → 缓存）和 FLOW 的「指标字典 → 事实库 → 计算口径」思路一致。可以借鉴 cube.js 的 metric YAML schema 来重构 FLOW 指标字典。
3. **问数能力**：Metabase 已经在做，是中端 BI 的标配。FLOW 应该加。
4. **国产化适配**：DataEase 在中国市场份额快速提升，FLOW 的部署方案要保持与信创 / 麒麟 OS 兼容。