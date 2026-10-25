---
doc_id: FLOW-INDEX-SCREENSHOTS-001
title: 项目实测与报告截图索引
doc_type: navigation
status: current
version: 1.6
created_at: 2026-09-04
updated_at: 2026-10-25
owner: FLOW
applies_to: repository
---

# 当前界面截图

本文件按采集批次记录真实页面截图；每个批次分别注明代码和数据来源。图片没有替换数值、拼接控件或使用生成图冒充页面。

## 离线驾驶舱导出主题复采（2026-10-25）

`cockpit-single-machine/offline-preview.html` 与同名 PNG 于视觉导出代码 SHA `d554bc317e8c948d776833b9868cdce4a9dd4c81` 重生成；截图对应当前隔离本机演示页面。数据仍是 synthetic 演示批次 `01a16e5a-7c2c-79ab-9608-522ba64cce88`，发行包 manifest SHA-256 `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`，8 个 KPI。该批只用于视觉输出核验，不能视为客户或真实企业数据。页面内嵌纸白、墨蓝、古金与字体 token，不依赖外部字体/CDN。

## 可复用视觉语言阶段截图矩阵（2026-10-24）

本批记录 A「高管编辑部」× C「财务报告画布」视觉语言应用中的全路由首轮矩阵。实际页面截图对应代码 SHA `28c0e7a29d7812106709947414c9a560f1c530b0`，20 个路由 × 桌面 1440、平板 1024、手机 390 三种视口，共 60 张；`results.json` 为每行记录对应截图路径、状态码、页面宽度、内容就绪、API 错误和浏览器错误，并列出 27 张不计入本矩阵的早期双下划线参考图，并登记 1 张显式打开指标依赖图标签的交互截图。

- 数据：隔离目录 `/tmp/flow-visual-audit-20261024` 中的大麦物流 synthetic 演示发行包，manifest SHA-256 `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`；不是客户或真实企业披露数据。
- 结果：60/60 路由视口 HTTP 200 且内容就绪、API 零错误、无页面级横向溢出及浏览器错误。按 20 张桌面截图完成首轮人工审阅；具体差距见[视觉覆盖报告](../../60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md#20-路由截图首轮差异盘点2026-10-24)。该结果不代表逐图表、交互态、可访问性或打印格式均已完成视觉验收。
- 入口：[视觉覆盖报告](../../60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md)、[逐路由结果与截图](../../60_delivery/verification/visual-language-20261024/results.json)、[桌面总览截图](../../60_delivery/verification/visual-language-20261024/cockpit--desktop.png)。
- README 中的旧视觉截图按历史批次保留；此矩阵仅用于本轮视觉差距检查。

## 单机原型收尾候选（2026-10-24，closeout-003bfa4b/）

采集日期：2026-10-24。当前代码从 SQLite 备份恢复到新隔离目录，在本机生产构建与 FastAPI 服务上重新采集。此批严格对应 7a 候选代码 SHA 与演示批次；静态 HTML 只展示截图和 API 固化响应，动态筛选/跳转/编辑需启动本地服务。

- 代码提交：`003bfa4b8a104b1c92bc6afb54c79c2f6965647d`。
- 数据源：大麦物流 synthetic 发行包，manifest SHA-256 `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`，批次 `01a16cf8-918b-75e8-9e85-415199207d7c`，指标快照 `01a16cfc-cf99-7843-ba4c-b07c4acdf981`。数据库来自一次性 `/tmp/flow-closeout-run-2f92fe4c` 恢复副本；不是客户真实月度数据，也不构成公开 C 级能力证明。
- 采集：九个路由各含桌面 1440px 与手机 390px 全页图，共 18 张；另存 11 个 JSON API 响应。viewport 横向溢出 0、浏览器错误 0、外网请求 0。
- 离线检查：`index.html` 的 9 张桌面图加载 9/9、静态链接断链 0、HTTP(S) 请求 0、浏览器错误 0。筛选、路由跳转、编辑与报告生成需要运行应用。
- 人工核看：桌面总览四项核心 KPI、收入/营业利润趋势、现金桥、杜邦与费用图均有实际图区；筛选条显示名称选项；390px 总览无水平溢出。账龄能力继续显示现有受限说明。

| 文件 | 内容 |
| --- | --- |
| [index.html](cockpit-single-machine/closeout-003bfa4b/index.html) | 九页桌面静态展示入口 |
| [manifest.json](cockpit-single-machine/closeout-003bfa4b/manifest.json) | 代码、数据批次、截图摘要与离线验收结果 |
| [api-responses.json](cockpit-single-machine/closeout-003bfa4b/api-responses.json) | 页面实采的 API 原始 JSON 响应 |
| [images/](cockpit-single-machine/closeout-003bfa4b/images/) | 九页桌面/手机实测截图 |

生成命令：`node scripts/export_cockpit_closeout_bundle.mjs --url http://127.0.0.1:3140 --output /tmp/flow-closeout-artifacts-003bfa4b`。

## 单机原型历史验收截图（cockpit-single-machine/）

采集日期：2026-10-20。此批为前一候选 SHA 的历史真实运行截图与离线 HTML 快照，不代表当前候选。

- 代码提交：`9ec0611562569b33bc3dac28c16445aa9470b150`（截图与离线快照基于此 SHA）。
- 数据源：大麦物流合成发行包，manifest SHA-256 `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`，批次 `01a154ea-455d-79fb-8521-072795629bec`；隔离数据目录 `/tmp/flow-stage7-20261020`，验证报告 19/19 通过。它是模拟经营数据，不是阿里巴巴、菜鸟或客户披露事实。
- 页面状态：真实总览显示营业收入、营业利润、毛利率、经营现金流、趋势图、现金流桥、杜邦拆解、费用结构和行动项；数据过期状态有醒目提示。金额按两位小数展示，订单数量按整数展示。
- 离线检查：`offline-preview.html` 是自包含静态快照；Playwright 以 `file://` 打开，8 项 KPI 与内嵌 API JSON 存在、图像加载成功、外部请求 0、页面错误 0。图表数据和来源说明可离线浏览；页面跳转、筛选等动态操作仍需启动本地应用。
- 生产构建和本地服务的控制台/页面错误为 0；手机视口未出现水平溢出。该验收使用一次性 `/tmp` 数据目录，不连接常驻演示数据。

| 文件 | 页面与状态 | 图片尺寸 |
| --- | --- | --- |
| [overview-desktop-2026-10-20.png](cockpit-single-machine/overview-desktop-2026-10-20.png) | 单机运行版 CFO 总览全页 | 1440 × 2350 |
| [overview-mobile-2026-10-20.png](cockpit-single-machine/overview-mobile-2026-10-20.png) | 手机总览全页，无横向溢出 | 390 × 4282 |
| [profitability-desktop-2026-10-20.png](cockpit-single-machine/profitability-desktop-2026-10-20.png) | 盈利能力和杜邦分析全页 | 1440 × 1777 |
| [offline-preview.png](cockpit-single-machine/offline-preview.png) | 离线 HTML 中嵌入的实际总览画面 | 1440 × 2350 |
| [offline-preview.html](cockpit-single-machine/offline-preview.html) | 可直接以浏览器打开的自包含离线报告 | 单个 HTML 文件 |

重新生成 HTML 的命令：`node scripts/export_cockpit_snapshot.mjs --url http://127.0.0.1:3000 --output docs/assets/screenshots/cockpit-single-machine/offline-preview.html`。运行和隔离验收细节见[单机视觉原型验收记录](../../60_delivery/verification/2026-10-20--single-machine-visual-static-acceptance-v1.md)。

## A+C CFO 驾驶舱实测截图（cockpit-visual/）

采集日期：2026-10-19。页面来自本轮工作树实现，运行于隔离大麦演示环境；浏览器视口固定为桌面 `1440 × 900`、手机 `390 × 844`，截图按全页高度采集。采集时记录 `pageerror` 与浏览器 console 的 warning/error 均为空；开发指示器仅在临时截图服务配置中关闭，不改变应用代码和页面行为。

- 数据库与服务：独立 Compose 项目 `flow-stage6-cockpit-20261019`（PostgreSQL/Redis/MinIO 独立端口与卷），API 与 Next.js 本地运行；不连接常驻开发库。
- 数据发行包：大麦物流合成发行包 manifest SHA-256 `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`；批次 `01a15463-cbbc-71dc-8f09-4b4cfdd586d8`；测试库为虚构企业数据，不是真实企业披露。
- 浏览器回归：Playwright `all CFO cockpit views render real charts without narrow-screen overflow`，9 路由 × 2 视口通过；总览四项 KPI 的完整趋势表逐项对照趋势 API。
- 截图记录的是真实应用页面。视觉概念图中的数字仍只是设计示意，不能与本批实测演示数据混用。

| 文件 | 页面与状态 | 视口 / 图片尺寸 |
| --- | --- | --- |
| [overview-desktop-2026-10-19.png](cockpit-visual/overview-desktop-2026-10-19.png) | 当前 CFO 总览：核心 KPI、收入/营业利润双轴趋势、现金流桥、杜邦、费用、来源和行动项 | 1440 × 900 / 1440 × 2296 |
| [overview-mobile-2026-10-19.png](cockpit-visual/overview-mobile-2026-10-19.png) | 同一总览的手机布局 | 390 × 844 / 390 × 4217 |
| [profitability-desktop-2026-10-19.png](cockpit-visual/profitability-desktop-2026-10-19.png) | 盈利能力、杜邦驱动、两期财年比较及来源行追溯 | 1440 × 900 / 1440 × 1777 |

本批截图通过 `/cockpit` 与 `/cockpit/profitability` 浏览器加载后直接采集。没有修饰图表、数值或页面控件。其准确代码提交与 CI 结果以阶段 6 验收记录为准。

## 2026-09-04 用户闭环截图（历史批次）

被展示的应用代码：`c1a59d1`。这些图片记录历史 UI，不代表当前页面样式。

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
