---
doc_id: FLOW-PLAN-DEEP-LINK-20260926
title: 全站超链接化（深链下钻）实施计划
doc_type: plan
status: active
version: 1.3
created_at: 2026-09-26
updated_at: 2026-09-26
owner: FLOW
depends_on: [FLOW-PLAN-CURRENT, FLOW-REVIEW-LINKABILITY-20260926]
acceptance_refs: [ui-deep-link-batch1, ui-deep-link-batch2, ui-deep-link-batch3]
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053]
applies_to: web-frontend
executable: true
supersedes: []
superseded_by: null
---

# 全站超链接化（深链下钻）实施计划｜2026-09-26

> 依据：用户 2026-09-26 确认[全站可链接性审计](../80_reviews/2026-09-26-ui-linkability-audit.md)
> 及其三批实施建议，要求把界面中所有可打通的内容全部改成可互相链接。
> 唯一状态与执行队列在 [CURRENT_ROADMAP](CURRENT_ROADMAP.md)；本文是实施规格。

## 1. 目标与原则

- 让任何有实体身份的界面元素（指标、Finding、快照、批次、维度值、报告、溯源页锚）
  都可以点击跳转到其权威页面/定位，URL 可分享、可复现。
- 只链接到**已存在的真实对象**；目标对象不存在时不渲染链接（诚实约束，同模块边界原则）。
- 不改动 `workflow-nav.tsx` 的导航 href 形态（navigation.spec.ts 精确选择器守卫）。
- 不做假深链：页面接收参数后必须真正定位到对应实体，定位失败显式提示而非静默忽略。

## 2. 批次一：接收端 + 纯前端链接（S + 5 页参数接收）

### 2.1 五个页面加 searchParams 接收（复制调查页模式）

| 页面 | 新增参数 | 定位行为 |
|---|---|---|
| `/metric-library` | `?focus={metric_code}` 或 `?entry={entry_id}` | 滚动定位并高亮对应指标卡片；卡片加 `id` 锚点 |
| `/statements` | `?report={report_id}` | 初始选中对应财报 tab（替代默认第一条） |
| `/reports` | `?snapshot={snapshot_id}` / `?focus={metric_snapshot_id}` | 初始选中对应快照/冻结候选 |
| `/data` | `?batch={batch_id}` | 恢复对应批次上下文（无批次列表端点，仅定位已有会话内对象；批次不存在时显式提示） |
| `/` 驾驶舱 | 读 `region_id`/`customer_segment_id`/`logistics_product_id`/`organization_id` | initialFilters 从 searchParams 初始化；**先修 `dashboard-app.tsx:53-56` 的 replaceState 覆盖问题**（有参初始化时不抹掉外来深链） |

### 2.2 纯前端链接（S 级，9 项）

1. 驾驶舱 findings-panel：Finding 标题/整行包 `<a href={investigation_path}>`；
2. investigations-index：Finding 标题单元格包同一 href；
3. investigation-view 检查行（对账失败/质量问题/阻断项）→ 页内锚点到证据/结论区（目标区加 id）；
4. statements review-panel 更正记录条目 → 页内锚点定位对应表格行（行加 id）；
5. metric-library 依赖指标 chip → 同页卡片锚点（依赖 2.1 的卡片 id）；
6. metric-governance-section 事件表 metric_code / 分录模板关联指标 → 卡片锚点；
7. data-workbench 发布完成态追加「前往经营分析/驾驶舱」引导链接；
8. reports-center 冻结候选区「回到 Investigation 流程」文案 → `/investigations` 链接；
9. FlowDataTable 评估加可选 `rowHref`（仅 investigations 列表启用），不动默认行为。

### 2.3 批次一随之解锁的 M 级跳转

指标卡→指标库、趋势点/快照号→报告中心、bridge driver→指标库、产品行/矩阵单元格/维度头→
驾驶舱筛选、状态条批次→数据页、analysis 身份行→statements、analysis/operations 指标行→指标库、
operations 冻结快照→报告中心、investigation 身份条四 ID→各自页面、reports↔statements/operations
互链、investigations 评分→analysis、图谱节点→指标卡片。

## 3. 批次二：轻后端补充

1. 指标库 `GET /metric-library/entries/{entry_id}` 详情端点（或列表按 entry 过滤）+ 前端
   `/metric-library?entry=` 定位消费；
2. MetricSnapshot / AnalysisRun 只读详情端点（供 `/reports?snapshot=`、investigation 身份条跳转）；
3. Copilot citations 点击定位到对应证据/源记录（页内定位）；
4. 覆盖矩阵列头（公司/期间）→ `/statements?report=`（载荷补 report_id 映射）。

## 4. 批次三：原文与源记录查看（重活）

1. 原始文件服务端点：按 `source_sha256`/`source_ref` 提供原始 PDF/工作簿的授权读取
   （只读、登记访问审计；不涉及生产发布）；
2. statements 溯源徽标/悬停卡「第 N 页」→ 原文 PDF 对应页（B3 闭环）；
3. 调查页源记录「来源」列（现为伪链接）→ 源单元格查看器；
4. 客观报告冻结 payload 保留 `page_number/page_anchor`，冻结 HTML 生成器内嵌回链；
5. ManagementWatchItem 补 finding_id/metric_code 关联字段，管理关注条目可下钻；
6. `GET /batches` 批次列表端点 + 数据工作台批次历史。

## 5. 验收

每批次收口标准：

1. `make lint && make typecheck && make test-web` 全绿；
2. `navigation.spec.ts` 既有 10 路由断言不破；
3. **新增深链 e2e**：每批至少覆盖——带参打开目标页能定位实体（断言高亮/选中态）、
   参数非法/对象不存在时显式提示、驾驶舱深链不被 replaceState 抹掉；
4. 大麦常驻栈回归：`make damai-demo-verify` 19/19 不破（页面结构变化不得破坏验证器）；
5. 文档门禁 `python3 scripts/check_docs.py --phase m1` 与 links check 通过；
6. 同 SHA CI 绿后更新 ROADMAP/工作包状态并推送。

## 6. 边界与不做

- 不改导航壳 href、不动模块边界诚实约束（designed 模块不加假入口）；
- 不改冻结报告历史内容；冻结 HTML 回链只作用于新冻结产物；
- 文件服务端点只做只读授权访问，不做在线编辑/下载权限放开；
- 不做搜索、不做全局图谱导航（超出本次范围）。

## 7. 执行状态（2026-09-26）

- **批次一：完成**。六页参数接收、9 项纯前端链接及 M 级下钻已实现；驾驶舱保留外来深链筛选。相关浏览器验收见 `apps/web/e2e/deep-links.spec.ts`。
- **批次二：实现完成，本地验收通过**。增加指标条目详情、MetricSnapshot/AnalysisRun 只读详情与授权血缘校验；Copilot 引用定位；公开覆盖矩阵列头按公司/期间解析财报 `report_id`，无映射时不生成链接。对应端点/前端/API 测试已纳入当前变更。
- 批次一、二的本地验证：API/安全相关 pytest **51/51**，Web Vitest **133/133**，TypeScript typecheck 通过、ESLint 0 errors（有一条既有 React Compiler warning），深链 Playwright **15/15**，OpenAPI/TypeScript 合同生成及 `check_docs --phase m1`、`--phase m6` 通过。
- 提交 `7976691` 上重新执行隔离大麦完整旅程：全新 Compose 数据库迁移、seed、存储读回，verify **19/19**，浏览器旅程 **9/9**。随后补强 `/data` 与 `/metric-library` 的真实展示断言：seed 批次出现在“最近的数据批次”中，点击后 `?batch=` 生效且行标记为当前批次；演示覆盖矩阵逐年显示 FY2025 **37/40**、FY2026 **40/40**，不是仅显示空壳或年份。两组新增断言后的隔离全旅程仍 **9/9**。该证据覆盖 Damai 主旅程，不代替其他每条路由的 API/页面覆盖矩阵。
- GitHub Actions run `36224649915`（代码基线 `29877d1`）dashboard、static-web、contracts、static-python、unit、investigation-e2e、module-boundaries-e2e 等已通过；`integration`、`data-contract`、`intake-e2e` 当时仍运行中。它不是本批次代码 SHA 的 CI 证据；本批次提交后的 CI 结果需另行核验。
- **批次三：实现完成，本地验收完成**。新增已登记公开财报 PDF 只读端点，严格按 `StatementSource.sha256` 解析对象键、读取时复验内容 SHA；沿用 `statement.source.read` RBAC durable decision audit，未登记 SHA fail closed。报表响应提供 `source_available`，页码徽标仅对真实已登记原件可点击并打开 PDF `#page=N`。源单元格查看器沿 Finding → ImportVersion → batch → fact → SourceRecord → SourceFile 逐层绑定，跨批次/未绑定 fact 返回 404；原始值与转换值只读展示。冻结新 objective payload 保留页码/锚点并记录 source 登记状态，HTML 新产物仅在原件可用时生成 PDF 页回链；既有冻结内容不重写。管理关注已有 `metric_code`，补上指标库深链；**不补造 `finding_id`**：当前四问工作台由 `StatementReport` 驱动，没有可证实的 Finding 关联，需在未来出现正式血缘映射后再开放。`GET /batches` 与批次历史原已交付，本轮确认后沿用，不重复实现。
- 本轮验证：原文 API / Investigation / objective freeze-render 相关 pytest 30/30，Web Vitest 142/142，`make lint` 0 errors（1 条既有 TanStack warning），mypy、TypeScript 与 contracts-check 通过；生产构建完整 E2E **91/91**（含深链 15 项）。独立 Clean Damai 验收通过：verify 19/19、可见性 API 43/43、浏览器旅程 9/9、对象读回 SHA/语义一致；文档 M1、链接门禁、脚本测试101/101、`git diff --check` 通过。全量 API suite **845 passed**（3 条告警，无失败）；本提交 SHA CI 尚待推送后核验。本状态不得解释为全站深链或 UX 工作包关闭。
- CI 纠偏：提交 `bc141444` 的 GitHub run `36247223015` 中 dashboard 状态测试从仓库根目录运行，旧 helper 基于 `process.cwd()` 解析 fixture，误指向 `/home/runner/work/fixtures/expected/`。改为基于 `__dirname` 定位仓库 fixture，并将 `dashboard-states.spec.ts` 纳入生产 E2E runner，固定验证该跨工作目录行为。纠偏后本地生产 E2E **93/93** 通过；修复 SHA `cef0c362` 的 GitHub Actions run `36248059559` **success**。
- 最终批次三证据：完整 API suite **845 passed**；工作树生产 E2E **93/93**；独立 Clean Damai verify **19/19**、可见性 **43/43**、浏览器 **9/9**、对象 SHA/语义校验通过；Web **142/142**、脚本 **101/101**；`cef0c362` 同 SHA CI 全绿。批次三已本地及 CI 验收，但 §5 全路由/页面状态/视口矩阵和 UX 工作包 Gate 1 尚未完成。
- 批次一、二、三全部具备本地实现证据后，仍以 §5 的全站路由/状态/视口覆盖及同 SHA CI、工作包 Gate 1 证据为最终关闭条件；不得将本轮局部来源闭环误报为全站深链计划及大麦 UX 工作包完成。
