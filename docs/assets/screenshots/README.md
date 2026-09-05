# 当前界面截图

采集日期：2026-09-04。被展示的应用代码：`c1a59d1`。全部图片为真实浏览器截图，没有替换数值、拼接控件或使用生成图冒充页面。

## 环境与来源

- 应用：Next.js 16.3.3 生产构建 + FastAPI，开启 AUTH_TOKEN 和单用户 Web 会话；
- 浏览器：Playwright 驱动已安装 Chrome；本会话未提供 Browser plugin，因此采用仓库 Playwright；
- 桌面视口：1600 × 1050，截图按页面实际高度完整采集；移动视口：390 × 844；
- 数据：独立 PostgreSQL 数据库，由 `scripts/seed_dashboard_demo.py --fresh-batch` 发布仓库内确定性物流示例的 12 个月指标及分析运行；
- 导入：上传仓库的 `external_logistics_nonstandard_v1.xlsx`，走真实画像、映射与清洗逻辑；仅源文件 S3 存储适配器替换为测试存储，未连接真实 S3 上传服务；
- 报告：演示 Finding 经真实状态机提交/批准后，在浏览器中执行冻结（HTTP 201），展示冻结报告列表与格式选择；未生成虚构产物，也未演示 PDF 成功发布；
- 客户、订单、金额与期间都是演示 fixture，不是客户数据。截图上的 2026-08 是演示分析期间，不是采集日期。

## 图片索引

| 文件 | 页面与状态 | 尺寸 |
| --- | --- | --- |
| [dashboard.png](dashboard.png) | 驾驶舱已加载：8 指标卡、12 月趋势、利润桥、4 个发现、产品/毛利矩阵 | 1600 × 1197 |
| [investigation.png](investigation.png) | 履约成本增加：驱动、证据、源记录、待提交结论 | 1600 × 1459 |
| [data-mapping.png](data-mapping.png) | 非标准示例上传后的映射确认 | 1600 × 2693 |
| [data-quality.png](data-quality.png) | 清洗校验 ready：0 阻断、0 警告、2 项对账通过 | 1600 × 1050 |
| [reports.png](reports.png) | 冻结报告 v1、生成格式与空尝试历史 | 1600 × 1050 |
| [login.png](login.png) | 单用户访问密码入口；未填入凭据 | 1600 × 1050 |
| [data-mobile.png](data-mobile.png) | 移动视口下的工作台准备/上传入口 | 390 × 844 |

## 操作与检查

浏览器实际执行登录、驾驶舱到 Investigation 的身份交接、文件选择、映射确认、清洗结果加载，以及报告冻结。页面 URL/标题和关键文字均核对，捕获的 `pageerror` 为空。人工检查驾驶舱、调查、报告、登录、移动入口与清洗截图；移动阶段文字会换行，导入和报告页面仍是功能优先的基础样式。

这些截图证明当前页面的样子与上述操作状态，不替代完整上传→计算→分析→签发→四格式发布的生产验收。截图中产品文案、数字格式和布局按实际实现保留。

## 后续更新

1. 使用独立演示库及已知 fixture，记录新的代码提交；
2. 通过真实页面达到目标状态，确保没有调试遮罩、密钥或客户信息；
3. 沿用稳定文件名并同步本说明的版本、尺寸和操作证据；
4. 图片更新作为文档变更提交，不触碰知识库原始图片档案。

## P5 图形化报告截图（p5/ 子目录）

采集日期：2026-09-06。本节图片**不是应用页面截图**，而是从 P5 真实财报反向解析实验的自包含 HTML 报告页面机械截取的板块画面。

- 来源页面：[顺丰 2026Q1 四表可视化分析](../../implementation/p5/sf_2026q1_report_view.html)、[腾讯 2Q2026 IFRS→Non-IFRS 调节分析](../../implementation/p5/tencent_2026q2_report_view.html)、[指标库 v0 评审台](../../knowledge-base/03_assets/visual_prototypes/metric-library-v0-review.html)；
- 采集方式：`node scripts/capture_p5_report_screenshots.mjs`（Playwright Chromium 无头浏览器，1440px 视口、2x 缩放，按 h2 板块边界纵向裁剪），未做数值替换、拼接或修饰；
- 数据性质：报告数字来自公开披露财报 PDF 的管道自动抽取（顺丰一季报/年报、腾讯业绩公告、京东物流公告），不是 FLOW 演示 fixture，也不是客户数据；
- 报告页面本身的数字在生成期做闭合校验（瀑布链、堆叠合计、杜邦乘积、分部加总），校验失败则构建失败、不产出图。

| 文件 | 内容 |
| --- | --- |
| [p5/sf-overview.png](p5/sf-overview.png) | 顺丰 2026Q1：KPI、五季度收入/归母净利润趋势、利润形成瀑布 |
| [p5/sf-dupont.png](p5/sf-dupont.png) | 顺丰 2026Q1：杜邦分析树（单季未年化、期末口径） |
| [p5/sf-structure.png](p5/sf-structure.png) | 营业总成本构成与资产构成 100% 堆叠（本期 vs 上期） |
| [p5/sf-peer.png](p5/sf-peer.png) | 顺丰控股 vs 京东物流同业对比（口径差异标注） |
| [p5/sf-cashflow.png](p5/sf-cashflow.png) | 资产/负债权益结构环形图、现金流三活动本期 vs 上年同期 |
| [p5/tencent-reconciliation.png](p5/tencent-reconciliation.png) | 腾讯 2Q2026：KPI、三期对比、IFRS→Non-IFRS 调节瀑布 |
| [p5/tencent-segments.png](p5/tencent-segments.png) | 腾讯 2Q2026：盈利率指标、收入结构环形图 |
| [p5/metric-library-overview.png](p5/metric-library-overview.png) | 指标库 v0 评审台总览（数据集统计与设计要点） |
| [p5/metric-library-relations.png](p5/metric-library-relations.png) | 评审台勾稽与分解关系页（含杜邦分解树） |
