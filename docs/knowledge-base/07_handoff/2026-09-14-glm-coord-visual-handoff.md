---
doc_id: FLOW-HANDOFF-20260914-GLM-VIS
title: GLM 协调者 · 报告风视觉系统统一（2026-09-14）
doc_type: navigation
status: current
version: 1.0
created_at: 2026-09-14
updated_at: 2026-09-14
owner: FLOW
applies_to: handoff
related: [HANDOFF.md, 2026-09-13-s01-session-handoff.md]
---

# GLM 协调者 · 报告风视觉系统统一 交接文档

- 写作时间：2026-09-14 上午
- 写作人：GLM 协调者会话（mvs_ce3323c6851e4dd3961e3cfe51647d70，session role: root）
- 读者：下一个接手的会话 / qiming 本人
- 配套阅读：`docs/00_start_here/PROJECT_STATE.md`、当前 `HANDOFF.md`、`scripts/build_static_library_site.py`

---

## 1. 当前任务与背景

用户主线诉求（**本轮始**）：「指标库 / 报表分析两个**在线**页面太朴素 → 把 Kimi 在静态站 + 看板 Widget 上做的报告风视觉（hero + KPI 卡带 + 覆盖矩阵 + verdict）反哺到 apps/web 真实页面，让线上/离线/看板三方视觉统一」。

随后追加：「当前 HTML 页面（docs/library/index.html）信息太分散 → 整合成 1~2 个大页面，加互链 + 更多可视化（颜色/图标/趋势/对比/饼图/柱图）」。

两条主线都已完成并推送。

---

## 2. 已完成内容

### 2.1 把报告风视觉反哺到在线页面（提交 `4be2c0f`）

| 文件 | 改动 |
| --- | --- |
| `apps/web/app/globals.css` | 新增共享设计令牌 `--rep-navy / --rep-red / --rep-ok / --rep-warn / --rep-zebra` 等 |
| `apps/web/app/statements/page.tsx` | 给 `/statements` 补 `AppShell`（之前是唯一漏的交互页，违反 FLOW 治理硬性要求） |
| `apps/web/components/metric-library/metric-library-app.tsx` | hero + 5 卡 KPI + 页脚 verdict；覆盖矩阵重写为列头进度条 + 行尾 A+/A/B+/B/C 等级 + 单元格热力 + 覆盖判断 verdict |
| `apps/web/components/metric-library/metric-library.css` | 新增 `.ml-hero / .ml-kpis / .ml-kpi / .ml-verdict / .ml-cov / .ml-grade` 视觉层；旧类名全部保留 |
| `apps/web/components/statements/statement-app.tsx` | 删除内嵌 `WorkflowNav`（AppShell 已提供）；加 hero + 本报告速览 verdict（不复读 KPI 数字避免文本冲突） |
| `apps/web/components/statements/charts/kpi-cards.tsx` | 每张 KPI 加圆形首字徽章；保留 `data-testid` 与原展示文案 `"X.XX 亿元"` |
| `apps/web/components/statements/statements.css` | hero / KPI seal / verdict / 深藏青表头 / 斑马纹 / 负数红字 |
| `apps/web/e2e/statements.spec.ts` | heading 断言改为新的"公开财报图形化分析" |

**验证**：
- vitest 64/64 通过（保留 `data-testid="statement-kpi"`、KPI 数字 `"741.42 亿元"`/`"10,236.70 亿元"`、4 个 `aria-label` 图角色、`getByText("流动比率")` / `getByText("事实 AST 执行")`）
- tsc 干净、eslint --max-warnings 0 干净

### 2.2 把静态资料库 11 个 section 整合成 1 个互链+可视化的"长滚动报告"（提交 `e114ae3`）

| 文件 | 改动 |
| --- | --- |
| `scripts/build_static_library_site.py` | 加 4 个 xref 工具 + 4 个 SVG 工具；新增执行摘要 section；12 个 section 全部加 ID/锚点 + 互链；初始化切到 `renderAll()`；新增 ~200 行 CSS |
| `docs/library/index.html` | 重新生成（524 KB） |
| `docs/library/widget.html` | 重新生成（看板 Widget 变体） |

**关键变化**：
- **页面模式**：`show(id)` 替换 innerHTML → `renderAll()` 一次性渲染全部 section + `scrollToSection()` 平滑滚动 + `IntersectionObserver` scroll-spy
- **互链**：4 个 xref 工具（xrefMetric / xrefAccount / xrefReport / xrefSection），共 **2480 个 `<a class="xref">`**
- **可视化**（内联 SVG，零外部依赖）：3 柱图（按公司覆盖 / 事实条数）+ 4 环形图（通用指标域 / 经营指标域 / 科目类别 / 余额方向）+ 3 sparkline（每家公司各期覆盖度趋势）
- **执行摘要**（新 section）：hero + 6 KPI 卡（每张脚注是"查看详情 →"超链）+ 红竖线 verdict（直接链接到最弱样本）+ 2 行 viz + 30 个指标快速索引网格
- **覆盖矩阵**：列头公司名变可点击、metric_code 变可点击、缺口格"缺 N"变可点击跳到对应 report 块
- **报告浏览器**：从下拉单选 → 14 份报告堆叠（每份独立 anchor + KPI 卡带 + 覆盖度 sparkline + 四表原文）

**验证**（headless Chromium，file:// 直开）：
- 12 个 section 全部 `display:block`
- 2480 个 xref / 3 柱 / 4 环 / 3 折线 / 0 JS 错误
- 点击 xref `#metric-current_ratio` → scrollY 2778，目标存在
- 点击 xref `#sec-reports` → scrollY 33633，目标渲染

---

## 3. 提交与推送

| 提交 | 描述 | 远程 |
| --- | --- | --- |
| `4be2c0f` | feat(web): propagate report-grade visual system to /metric-library and /statements | origin/codex/s01-parallel-integration |
| `e114ae3` | feat(library): unify 11 sections into 1 scrollable report with xrefs and SVG visualizations | origin/codex/s01-parallel-integration |

本地分支：`glm-coord`，与 `origin/codex/s01-parallel-integration` 同步。

---

## 4. 卡住的问题 / 待跟进

### 4.1 不在本会话范围
- **e2e 守护**：本会话修改了 `apps/web/e2e/statements.spec.ts`（heading 断言），但没有跑过完整 e2e（需要 docker compose 基础设施 `make infra-up`）。其他 e2e（navigation / metric-library-governance / statements-review / dashboard-visual）不涉及本次改动，理论上不应受影响，但 CI 上需要确认。
- **现存 13 个未暂存文件 + 1 个未跟踪文件**（`scripts/seed_dev_principal.py`、Makefile、compose.yaml、scripts/test_*.sh、services/api/tests/ 等）：来自其他并行会话（Kimi / Sol / route-policy / security-audit），不是本任务产出，**未纳入本会话提交**。下一会话接手时先 `git fetch` + `git status` 判断归属。

### 4.2 已知数据/口径瑕疵（线上已修复展示，事实库未改）
- 阿里 FY2019 反向解析把季度数对上了年度基数 → 同比 +2234% 等荒谬值。静态站和线上的覆盖矩阵都用 `n.m.`（不具可比性）替代，但事实库原值未变，**重新跑 `p5_query_facts.py` 会复现**。如果要彻底清理，需要在别名映射里加 `abs` 或 `disable_yoy` 标志。
- 比率指标的"较期初"展示是百分点差而非相对幅度（已修），但口径定义 `metric_dictionary_v1_1.yaml` 里的 `decompositions` / `caliber` 字段没动 —— 业务侧若要长期保持一致，需要在 dataset YAML 里加约束。

### 4.3 看板 Widget 视觉一致性
- `widget.html` 用了 WIDGET_OVERRIDES CSS 段（追加于末尾）覆盖 Kimi 设计令牌，让离线版和看板版视觉一致。但 **`viz-row` / `viz-card` / `.xref` 是新增的类**，没在 WIDGET_OVERRIDES 里专门处理，目前在看板里走默认深藏青/红。**若看板主题色变化，需要补变量映射**。

---

## 5. 下一步计划（建议给下一会话）

1. **e2e 验证**：本会话修改了 `e2e/statements.spec.ts` 的 heading 断言，但未跑。CI 上跑一次 `scripts/test_user_closure_e2e.sh` / `scripts/test_dashboard.sh` 确认无回归。
2. **看板 Widget 主题适配**：补 WIDGET_OVERRIDES 让 `.xref` / `.viz-card` / 状态徽标也走 Kimi 设计令牌，规避主题色冲突。
3. **线上 /metric-library 进一步统一**：
   - 覆盖矩阵已经重做，但**点击 metric 行的公司列头应能跳到 /statements 对应公司**（现在只跳到同页 report 块）。可在 `metric-library-app.tsx` 的 CoverageSection 加 `<a>` 包公司列头，`target="_blank"` 打开新标签到 `/statements?company=...`。
   - **「指标快照」快速索引**（`metric-quick` grid）样式可以同步到线上 /metric-library 顶部。
4. **真实数据瑕疵清理**（4.2 提的）—— 修别名映射或在 metric 字典里加 `disable_yoy` 标志，避免静态站重生成时 `n.m.` 标记需要手动重写。
5. **本会话没动 /statements 的 KPI 卡带视觉**（虽然加了 seal，但没把"资产负债率 / 毛利率"等比率指标也用 sparkline 或趋势徽标）。可在 `reportKpis` 之后加一个迷你趋势区。

---

## 6. 踩过的坑

### 6.1 tsc / vitest 同名重复声明（指标库）
- 多次编辑 metric-library-app.tsx 时，`COVERAGE_COMPANY_NAMES` 被声明两次，`coverageGrade` 也是。`tsc --noEmit` 会报 `TS2451: Cannot redeclare block-scoped variable`。**修复**：每次大改完跑一次 `tsc --noEmit -p .`，比 vitest 早暴露问题。
- 修法：保留一份、删另一份；或用模块级常量集中放置。

### 6.2 vitest 文本节点匹配（指标库覆盖矩阵 verdict）
- 一开始在 verdict 文案里同时引用了 metric 名字（如 "（流动比率）"），导致 `getByText(/流动比率/)` 匹配到 2 个元素（表格 + verdict）→ 测试抛"多元素匹配"。**修复**：verdict 只用 `metric_code`（如 `current_ratio`），名字留给表格。
- 同样的坑：把 KPI 数字（如 "741.42 亿元"）也写进 verdict，触发"多元素匹配"。**修复**：verdict 改写为维度描述（"已抽取 收入规模 / 盈利水平 / 经营现金流 3 个核心维度"），不复读 KPI 数字。

### 6.3 KPI 比率/百分比展示为"相对幅度"还是"百分点"
- 一开始 verdict 用百分比相对幅度，导致阿里 FY2019 同比 +2234% 这种荒谬值。**修复**：静态站和线上都改为百分点差（`pct` 单位，`.toFixed(1)` 直接相减），但保留 `n.m.`（不具可比性）作为异常值标记。

### 6.4 静态站 donut SVG 缺 class
- `barChart` 和 `sparkline` 在 SVG 上加了 `class="viz-bars" / "viz-spark"`，但 `donutChart` 只在 `<div class="viz-donut">` 包装层加了类，SVG 本身没加。导致 e2e `svg.viz-donut` 选择器匹配 0 个。**修复**：补 `class="viz-donut__svg"`。

### 6.5 Git 推送代理
- `HTTPS_PROXY=http://127.0.0.1:1082` 配了但本地代理进程没启动，git push 报 "Failed to connect to 127.0.0.1 port 1082"。**修复**：push 时清空代理 `HTTPS_PROXY="" HTTP_PROXY="" https_proxy="" http_proxy="" git push ...`。

### 6.6 `show(id)` 仍被旧代码引用
- 把页面模式从"单 section 切换"改为"全 section 滚动"时，忘了把 `renderFacts` / `renderReports` 里 `<select onchange="...show('reports')">` 一起改。这些事件 handler 引用了已删除的 `show()` 函数。**修复**：改用 `factRender()` / `scrollToSection()` 重渲染表格内容（不重建 section）。

### 6.7 静态站 dataset_id 链接方向
- 执行摘要里把"数据集导航"表里的 dataset_id 链接到 `#sec-{id}`（section 锚点），而不是 `#dataset-{id}`。原因是 section 已经有 `id="sec-overview"`，重复锚点意义不大。如果后续要做 dataset 详情页，再补二级锚点。

### 6.8 工作区并发
- 本会话开始时工作区已有 12 个未暂存文件 + 1 个未跟踪文件（来自 Kimi / Sol / route-policy / security-audit 的并行会话），`git status` 一片脏。**纪律**：只 `git add` 自己改过的文件，**绝不** `git add -A` 或 `git add .`。
- 本会话两次推送都成功（`4be2c0f` / `e114ae3`），但推送时 `git status` 仍脏——脏的都不是我引入的，是其他并行会话的 WIP。
- 推送命令走 `git push origin glm-coord:codex/s01-parallel-integration`（指定源:目标分支），不是 `git push origin HEAD`，因为本地分支 `glm-coord` 与 `origin/codex/s01-parallel-integration` 是 tracking 关系但 `HEAD` 可能错位。

### 6.9 并发分支收口（2026-09-14 上午，用户要求"所有并发分支合并到主分支"）
- **做法**：本地 `main` 从 `aade2e2` fast-forward 22 个 commit 到 `c806033`（= `origin/codex/s01-parallel-integration` = `origin/main` 当时的 SHA），然后用 `--no-ff` 合并 5 个有独有 commit 的分支。
- **合并结果**：5 个 merge commit 落在 main（`09333bc` / `13a03ca` / `f5d9c52` / `5e8b925` / `91bfb56`），把 4 个 codex/s01-* 分支独有的 13 个 commit 拉进来。`origin/main` 从 `c806033` 推进到 `91bfb56`。
- **故意跳过 `codex/s01-route-policy` v1**：v1 的 `0841ff9 feat(security): enforce policy across sensitive routes` 已被 v2（`997c1ab feat(security): route policy registry, loaders and require_action per approved V1.1`）按"approved V1.1"路线取代。强行合并 v1 会在 `audit.py / authorization.py / principal.py / settings.py / test_auth_boundary.py` 五个 security 文件上与 v2 冲突，**等同于回退到被拒绝的设计**。分支仍存在（`cf90df0`），可作为审计证据，但不应合入 main。
- **没合并的分支（已无需合并）**：`codex/s01-full-verification` 和 `codex/s01-module-boundaries` 共享同一组 commit（同一 SHA `a4051ea`），合并其一即覆盖。
- **验证**：`make contracts-check` 干净、`tsc --noEmit` 干净、`vitest run` 64/64 通过。

---

## 7. 关键命令速查

```bash
# 重生成静态站（uv 环境，pyyaml 按需拉）
cd /Users/qiming/workspace/FLOW
uv run --with pyyaml python3 scripts/build_static_library_site.py

# 跑线上 vitest
cd apps/web && npx vitest run

# tsc + eslint
cd apps/web && npx tsc --noEmit -p .
cd apps/web && npx eslint --max-warnings 0 components/metric-library components/statements app e2e

# headless 浏览器实测（Python playwright 装在 pyenv 3.13.3）
PATH=/Users/qiming/.pyenv/versions/3.13.3/bin:$PATH python3 -c "..."

# 推送（清代理）
HTTPS_PROXY="" HTTP_PROXY="" https_proxy="" http_proxy="" \
  git push origin glm-coord:codex/s01-parallel-integration
```

---

## 8. 文件清单（本会话产出）

### 修改
- `apps/web/app/globals.css`
- `apps/web/app/statements/page.tsx`
- `apps/web/components/metric-library/metric-library-app.tsx`
- `apps/web/components/metric-library/metric-library.css`
- `apps/web/components/statements/charts/kpi-cards.tsx`
- `apps/web/components/statements/statement-app.tsx`
- `apps/web/components/statements/statements.css`
- `apps/web/e2e/statements.spec.ts`
- `scripts/build_static_library_site.py`

### 生成
- `docs/library/index.html` (524 KB)
- `docs/library/widget.html`

### 新增
- `docs/knowledge-base/07_handoff/2026-09-14-glm-coord-visual-handoff.md`（本文件）
