---
doc_id: FLOW-REVIEW-LINKABILITY-20260926
title: 全站界面可链接性审计（超链接改造清单）
doc_type: review
status: open
version: 1.0
created_at: 2026-09-26
updated_at: 2026-09-26
owner: FLOW
applies_to: web-frontend
subject_ref: main@58c5a5d
findings: [ui-linkability-audit]
---

# 全站界面可链接性审计（2026-09-26）

> 缘起：用户反馈界面大部分是静态文字和指标，不可点击下探；要求扫遍全站，
> 找出所有「语义上应该可以互相链接」的内容。本文是审计清单，不是实施计划；
> 实施前须按计划铁律另写实施计划文档。

## 0. 总体结论

- 全站 10 条交互路由中，**只有 `/investigations/[findingId]` 一个真正的深链接收端**
  （路由段 + `batch_id`/`metric_snapshot_id`/`analysis_run_id` query，后端 409 身份校验）。
  其余页面的 `page.tsx` 均为无参薄壳，组件内零 `useSearchParams`。
- 驾驶舱筛选器**只写不读** URL（`history.replaceState` 会抹掉外来深链）——改造 `/` 的
  读参能力时必须先处理这段逻辑。
- 标识符瓶颈很小：metric_code、snapshot_id、batch_id、finding_id、维度 id、entry_id
  在 API 响应里基本现成。**主要瓶颈是目标页面不读参数，其次是少数对象缺详情端点。**
- 共享表格 `FlowDataTable` 单元格支持任意 ReactNode，加链接列无需改组件；
  但它不支持整行点击（无 `rowHref`/`onRowClick`）。

## 1. 改造量级定义与统计

| 量级 | 含义 | 数量 |
|---|---|---|
| S | 纯前端即可（href 现成或页内锚点） | 约 9 |
| M | 需目标页支持 URL 参数定位 | 约 27 |
| L | 需后端补字段/新端点 | 约 11 |

**杠杆点**：给 `/metric-library`、`/statements`、`/reports`、`/data`、`/` 五个页面加
searchParams 接收能力（调查页模式可直接复制），一次性解锁约 15 个 M 级下钻。

## 2. 分页清单

### 2.1 `/` 驾驶舱首页

| 元素 | 位置 | 形态 | 可用标识符 | 建议目标 | 量级 |
|---|---|---|---|---|---|
| 指标卡整体（标题+主值+对比值） | components/dashboard/metric-grid.tsx:15-24 | 静态 | metric_code | `/metric-library?focus={metric_code}` | M |
| 趋势图折线点/明细表月份 | trend-panel.tsx:19-28 | 静态 | month、metric_snapshot_id | `/reports?focus={snapshot_id}` | M |
| 利润桥 driver 柱 | profit-bridge-panel.tsx:11 | 静态 | driver_code | `/metric-library?focus=` / `/analysis` | M |
| 驱动合计对账状态 | profit-bridge-panel.tsx:13 | 静态 | 无 id | `/reports` | M（低优先） |
| Finding 标题/整行 | findings-panel.tsx:10 | 静态（右侧已有「进入调查」链接） | finding_id、investigation_path | `/investigations/{finding_id}`（href 现成） | **S** |
| 产品行（名称+各列） | product-performance-table.tsx:8 | 静态 | logistics_product_id | `/?logistics_product_id=` 自身筛选下钻 | M |
| 毛利矩阵单元格 | margin-matrix.tsx:17 | 静态 | customer_segment_id+logistics_product_id | `/?customer_segment_id=…&logistics_product_id=…` | M |
| 矩阵行/列维度名 | margin-matrix.tsx:16 | 静态 | DimensionOption.id | 同上（单维筛选） | M |
| 数据状态条（批次/质量/对账） | data-status-bar.tsx:7-9 | 静态 | batch_id、import_version_id | `/data?batch=` | M |
| 状态条快照/引擎版本 | data-status-bar.tsx:10-11 | 静态 | metric_snapshot_id、analysis_run_id | `/metric-library` / `/reports` | M |

### 2.2 `/analysis` 四问工作台

| 元素 | 位置 | 形态 | 可用标识符 | 建议目标 | 量级 |
|---|---|---|---|---|---|
| 身份行「公司·期间·单位」 | four-question-workbench.tsx:112-115 | 静态 | report_id | `/statements?report={id}` | M |
| 管理关注条目 | :122-129 | 静态 | code、direction（无关联 id） | 下钻需后端在 ManagementWatchItem 补 finding_id/metric_code | **L** |
| 指标行（metric_code+值） | :143-151 | 静态 | metric_code + report_id | `/metric-library?focus=` | M |

### 2.3 `/operations` 经营概览

| 元素 | 位置 | 形态 | 可用标识符 | 建议目标 | 量级 |
|---|---|---|---|---|---|
| 冻结结果「版本·快照 id·指纹」 | operations-overview.tsx:262-267 | 静态 | snapshot_id | `/reports?snapshot=` | M |
| 管理关注条目 | :275-282 | 静态 | 同 analysis，无关联 id | 同 L 改造 | **L** |
| 主题内指标行 | :307-340 | 静态 | entry_id | `/metric-library?focus={entry_id}` | M |
| 来源证据行（source_ref·页码·sha256） | :322-333 | 静态 | source_ref、source_page、source_sha256 | 原文档查看器（路由与端点均不存在） | **L** |

### 2.4 `/investigations` 列表与详情

| 元素 | 位置 | 形态 | 可用标识符 | 建议目标 | 量级 |
|---|---|---|---|---|---|
| Finding 标题单元格 | investigations-index.tsx:38-43 | 静态（操作列已有链接） | finding_id 等四元组，href 已拼好 | 标题包成同一 href | **S** |
| 评分 total_score | :78-89 | 静态 | analysis_run_id | `/analysis?run_id=`（目标需加参） | M |
| 身份条四个 ID | investigation-app.tsx:248-270 | 静态 | finding/batch/snapshot/run id | `/data?batch_id=`、`/reports?snapshot=`、`/analysis?run_id=`（均需加参） | M×3 |
| 驱动明细行 | investigation-view.tsx:229-238 | 静态 | driver_code | 贡献源记录过滤视图（目标不存在） | M |
| 检查行（对账失败/质量/阻断） | :301-340 | 静态 | reconciliation_code 等 | 页内锚点到证据/结论区 | **S** |
| **源记录「来源」列（伪链接）** | :351-352, 382-386 | **文案承诺"点击来源查看原始单元格"但实际不可点** | fact_id、sheet、行列坐标 | 源单元格查看器（前后端均无） | **L** |
| 证据条目（object_id/digest） | :519-537 | 静态 | evidence_id、object_id | 证据对象详情（端点不存在） | **L** |
| Copilot 引用 citations | copilot-panel.tsx:99-105 | 静态 | citation 对象引用 | 点击定位对应证据/源记录 | M |
| 更正记录条目 | review-panel.tsx:108-117 | 静态 | statement_type/item_name/column_key | 页内锚点定位表格行（需加行 id） | **S** |

### 2.5 `/reports` 报告中心

| 元素 | 位置 | 形态 | 可用标识符 | 建议目标 | 量级 |
|---|---|---|---|---|---|
| 客观财报条目追加「查看分析」 | reports-center.tsx:261-272 | 已链冻结 HTML | report.id | `/statements?report={id}` | M |
| **冻结 HTML 内部零超链接** | statements/objective_report_html.py（服务端生成） | 静态 | payload 有 source_ref/页码 | 冻结 HTML 内回链 | **L**（生成器+目标页） |
| 经营报告快照行 | :293-305 | 静态 radio | id、statement_report_id、payload_hash | `/operations?report=` | M |
| 冻结候选提示文案 | :387-404 | 静态 | — | 「回到 Investigation 流程」加链接 | **S** |
| 报告快照行（v/标题/日期） | :413-425 | 静态 radio | id、metric_snapshot_id | 快照详情/预览（目标不存在） | M |

### 2.6 `/statements` 报表分析

| 元素 | 位置 | 形态 | 可用标识符 | 建议目标 | 量级 |
|---|---|---|---|---|---|
| 财报选择 tabs 不落 URL | statement-app.tsx:295-308 | button+state | report.id | `/statements?report={id}`（可分享深链） | M |
| source_ref / 源文件 SHA | :171-174 | 静态 | source_ref、source_sha256 | 原始 PDF 查看/下载（无端点） | **L** |
| **溯源悬停卡「第 N 页」** | provenance-badge.tsx:32-73 | tooltip 不可点击 | page_number、page_anchor、source_ref | 链接到原文 PDF 对应页（B3 闭环缺口） | **L** |
| 「p{page}」溯源徽标 | provenance-badge.tsx:104-116 | onClick 只弹 tooltip | 同上 | 同上 | **L** |

注：B3 溯源数据链路已通（迁移 0029 → API → UI），止步于悬停层，缺原文查看器与文件端点。

### 2.7 `/metric-library` 指标库

| 元素 | 位置 | 形态 | 可用标识符 | 建议目标 | 量级 |
|---|---|---|---|---|---|
| 指标卡片（metric_code+名称） | metric-library-app.tsx:155-217 | 静态；entry_id 不展示 | entry_id、metric_code | `/metric-library?entry=` 或卡片锚点 | M |
| 依赖指标 chip | :174-176 | 静态 | metric_code | 跳对应卡片（需锚点 id） | **S**/M |
| 图谱节点点击只高亮 | dependency-graph.tsx:296 | onClick 不跳转 | metric_code | 节点跳指标详情 | M |
| 覆盖矩阵列头（公司/期间） | metric-coverage-section.tsx:256-271 | 静态 | company、period（无 report_id） | `/statements?report=`（需后端补映射） | **L** |
| 覆盖矩阵单元格 | :279-301 | 静态 | metric_code+company+period | 取数明细下钻（端点不存在） | **L** |
| 治理事件表 metric_code | metric-governance-section.tsx:155-164 | 静态 | metric_code/entry_id | 指标卡片锚点 | **S**/M |

注：`semantic-context` 端点按合同返回 entry_id，但前端无任何消费者，无按 entry_id 的详情路由。

### 2.8 `/data` 数据工作台

| 元素 | 位置 | 形态 | 可用标识符 | 建议目标 | 量级 |
|---|---|---|---|---|---|
| 无批次列表/历史（刷新即丢） | data-workbench.tsx 整页 | 批次/SHA/importVersion 在 state 从不展示 | batch.id、source.sha256、importVersion.id | 批次历史列表（缺 GET /batches 列表端点） | **L** |
| 转换规则条目 | :288-292 | 静态 | rule_id、rule_version | 规则注册表（不存在） | M |
| 质量问题条目（sheet/行/列） | :299-316 | 静态 | issue.id、行列坐标 | 源单元格查看器（同调查页 L） | **L** |
| 发布完成态 | :336-343 | 仅下载按钮 | importVersion.id | 追加「前往指标计算/经营分析」引导链接 | **S** |

### 2.9 `/internal`、`/public`、`/login`

无需改造：`/internal`、`/public` 的模块卡与功能入口已是链接；designed 模块卡的
「规划中」无链接是模块边界诚实约束的设计使然，**不应**加链接。

## 3. 后端缺口汇总（L 级的前提）

1. MetricSnapshot / AnalysisRun 无 GET 详情端点（实体在 DB，契约只作引用）；
2. 指标库无 `GET /entries/{entry_id}` 详情；entry_id 仅用于 POST 动作；
3. 财报行项目无行级 id 外泄（仅 item_name/sort_order + 页锚）；
4. 原始 PDF/源工作簿无文件服务端点（`source_ref` 只是路径字符串）——
   这是 B3 页锚跳转、源单元格查看器、证据对象详情三个 L 项的共同根因；
5. 客观报告冻结 payload 丢弃 `page_number/page_anchor`（publishing/objective_freeze.py:188-217），
   冻结产物无法自链源页码；经营概览冻结无此问题（payload 完整保留 source 字段）；
6. 管理关注条目（ManagementWatchItem）无 finding_id/metric_code 关联字段；
7. 覆盖矩阵载荷不含 report_id 映射；无批次列表端点（`GET /batches`）。

## 4. 建议的实施分批（供实施计划参考，非执行依据）

- **第一批（纯前端，约 9 项 S + 5 页参数接收）**：Finding 标题/整行链接、检查行页内锚点、
  更正记录行锚点、依赖 chip 锚点、发布后引导链接；给 `/metric-library`、`/statements`、
  `/reports`、`/data`、`/` 加 searchParams 接收（复制调查页模式），同步处理驾驶舱
  replaceState 覆盖问题。这批做完约 15 个 M 项随之解锁。
- **第二批（前端为主 + 少量后端）**：指标库 entry 详情、快照/运行详情端点、
  citations 定位、覆盖矩阵列头映射。
- **第三批（后端重活）**：原始文件服务端点 + 源单元格/PDF 页锚查看器（B3 闭环）、
  冻结 payload 保留页锚、冻结 HTML 内回链、管理关注条目关联字段、批次列表端点。

## 5. 守卫与测试注意

- `apps/web/e2e/navigation.spec.ts` 只断言导航壳与 10 条静态路由，给内容区加 query
  深链无需改它；但若把导航 href 改成带 query 形式，精确选择器会失配；
- 建议为「深链接收」新增 e2e 断言（带参打开页面能定位到目标实体），当前守卫
  覆盖不到这类回归。
