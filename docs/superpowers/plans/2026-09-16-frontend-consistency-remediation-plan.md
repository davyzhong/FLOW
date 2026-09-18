---
doc_id: FLOW-PLAN-FE-CONSISTENCY-REMEDIATION-20260916
title: FLOW 全页面前端一致性修复与升级实施计划
doc_type: plan
status: active
version: 1.4
created_at: 2026-09-16
updated_at: 2026-09-17
owner: FLOW
depends_on:
  - FLOW-PLAN-FE-DESIGN-UPGRADE-20260915
acceptance_refs:
  - frontend-route-state-viewport-matrix
  - frontend-same-sha-green
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: web-frontend-consistency
decision_refs:
  - D052
  - D053
source_refs:
  - docs/superpowers/plans/2026-09-15-frontend-design-upgrade-proposal.md
  - docs/competitive/2026-09-15-frontend-patterns-research.md
  - AGENTS.md
subject_ref: main@ec6450aa375cd8515e509d9c50e6c298a1399b8f
---

# FLOW 全页面前端一致性修复与升级实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task by task.

**Goal:** 修复当前前端改造中已经出现的回归，建立可执行、可验证的全页面一致性标准，再按页面批次完成迁移，使 FLOW 的全部用户界面在结构、状态反馈、交互、响应式与证据表达上形成同一种产品体验。

**Architecture:** 保留现有 AppShell 和工作流导航作为唯一页面外壳；将视觉与交互规则收敛到共享组件和设计令牌；页面只负责业务编排，不再复制基础表单、表格、状态、来源说明和操作反馈。验收采用“路由 × 状态 × 视口”矩阵，并以自动化测试、截图审查和同一提交 CI 结果共同判定。

**Tech Stack:** Next.js App Router、React、TypeScript、Tailwind CSS、Vitest、Testing Library、Playwright；现有 Radix/Lucide/TanStack 依赖按实际需要使用，不为追求技术栈完整度而强制引入。

---

## 0. 使用说明与执行边界

这是一份“随时可启动”的静态实施计划，不是第二份项目路线图，也不代表其中的代码任务已经完成。

- 唯一项目执行入口仍是 ../../50_plans/CURRENT_ROADMAP.md。
- 启动本计划时，由主协调者先核对 PROJECT_STATE、CURRENT_ROADMAP、当前 HEAD、未提交改动和 CI 状态。
- 用户发出“启动前端一致性修复计划”或等价明确指令后，执行者从 Task 0 开始。
- 每个任务先补失败测试或失败验收，再实施，再跑对应验证；不得先删旧样式、后迁移页面。
- 每个任务仅提交本任务文件。工作区中他人未提交的文件必须保留，禁止顺手暂存。
- 一次只允许一个 Agent 负责集成与状态更新。可并行的页面批次也必须使用独立 worktree，并在同一集成基线上验证。
- 本计划不改变 FLOW 的产品战略、业务边界、财务口径或权限模型。

### 启动命令

    git status --short
    git rev-parse HEAD
    git fetch origin
    python3 scripts/check_docs.py --phase m1

若工作区不干净，先确认每个改动的所有者；不得以清理工作区为理由覆盖用户或其他 Agent 的文件。

---

## 1. 对话、诊断与评审结论

### 1.1 用户要求

本计划承接的核心问题是：

1. 所有页面是否已经修改并形成一致的前端体验；
2. 如果没有，既有前端升级方案是否完整、执行是否跑偏；
3. 将对话结论、诊断证据和修复建议沉淀为单一可执行文档，便于后续交给单一 Agent 修正。

### 1.2 审查基线与方法

- 代码基线：main@ec6450aa375cd8515e509d9c50e6c298a1399b8f。
- 文档基线：2026-09-15 前端设计升级方案 V2.0 与前端模式研究。
- 浏览器审查：1440×1000 桌面视口，覆盖登录页和十个业务入口。
- 移动审查：390×844 视口，检查横向溢出和触控目标。
- 代码审查：AppShell、全局布局、工作流导航、共享组件、页面 CSS、组件测试和 E2E。
- 测试审查：前端 Vitest 共发现 19 个文件、72 项测试；当时结果为 71 通过、1 失败。

### 1.3 总体结论

**不是所有页面都已完成一致性改造。**

当前结果属于“全局外壳基本统一、部分共享组件已落地、页面内容层迁移不完整”。现有方案的产品方向正确，但还不足以作为全页面收口合同；更关键的是，实际执行已经违反其“先迁移页面、再删除旧 CSS”的顺序约束，导致 Data 等页面出现明显视觉回归。

### 1.4 已确认问题清单

| 编号 | 严重度 | 已确认事实 | 影响 | 本计划处理 |
|---|---:|---|---|---|
| FE-01 | P0 | data-workbench.css 已大幅删除旧规则，但 data-workbench.tsx 仍使用旧类名和原生控件 | 数据工作台接近浏览器默认样式 | Task 2 |
| FE-02 | P0 | 报告页仍有原生控件，并直接暴露英文错误 | 核心工作流体验断裂 | Task 2、Task 3 |
| FE-03 | P0 | 登录页采用整页行内样式和原生输入控件 | 登录与主应用不是同一产品语言 | Task 1 |
| FE-04 | P0 | 根布局在存在认证信息时全局渲染“退出登录”，登录页和每个业务页均可能出现孤立页脚 | 导航层级、可用性和观感异常 | Task 1 |
| FE-05 | P0 | 多个页面收到 403 后直接显示原始错误，处理方式不一致 | 用户无法判断权限、数据或系统故障 | Task 3 |
| FE-06 | P0 | Statements 在 390px 视口出现 body 599px 横向溢出 | 移动端不可用 | Task 5 |
| FE-07 | P1 | 各页存在 11–18 个小于 44px 的可交互目标 | 触控与无障碍体验不足 | Task 5 |
| FE-08 | P1 | ProvenanceBadge 依赖 hover，缺少稳定的键盘/触控打开方式和实际来源跳转 | 核心“可追源”价值表达不完整 | Task 4 |
| FE-09 | P1 | FlowDataTable、EmptyGuide、Provenance 等共享组件只覆盖少数页面 | 组件存在但未形成系统能力 | Task 3、Task 4、Task 6 |
| FE-10 | P1 | Metric Library 错误态缺少稳定页面标题；Operations、Public、Internal 仍是过渡性样式 | 页面成熟度不一致 | Task 6、Task 8 |
| FE-11 | P1 | navigation.spec.ts 只检查导航和链接，不检查状态、响应式或视觉一致性 | 自动化门禁无法阻止此次回归 | Task 0、Task 9 |
| FE-12 | P1 | dashboard-content 测试仍断言旧导航文案“分析与归因” | 当前前端测试并非全绿 | Task 0 |

### 1.5 对既有方案的评审

既有方案以下方向继续保留：

- 以证据完整性、工作流优先、渐进披露和高信息密度为设计原则；
- 不把产品改造成通用 BI 仪表盘；
- 保留 AppShell 和工作流导航；
- 采用渐进式 Tailwind、共享组件与表格能力迁移；
- 财务事实、来源、口径和人工确认在界面中保持可见。

既有方案以下部分必须补强：

- 增加完整页面清单和负责人；
- 增加“路由 × 状态 × 视口”验收矩阵；
- 把登录、退出、403、错误态、空态、加载态纳入设计系统；
- 增加移动端、键盘、触控目标和横向溢出标准；
- 增加同一提交的截图、自动化和 CI 门禁；
- 把迁移顺序写成硬约束，禁止先删旧样式；
- 将“视觉走查”改成有产物、有命名、有审查结论的正式步骤。

---

## 2. 页面覆盖矩阵

启动时必须以实际路由清单重新生成本表；下表是本次审查发现的最低覆盖范围。

| 路由 | 页面角色 | 当前判断 | 必验状态 | 批次 |
|---|---|---|---|---|
| /login | 身份入口 | 未统一 | 默认、校验失败、登录失败、处理中 | P0 |
| / | 经营总览 | 部分统一 | 正常、空、加载、错误、403 | P2 |
| /data | 数据接入 | 明显回归 | 正常、映射、上传失败、空、403 | P0 |
| /investigations | 调查列表 | 部分统一 | 正常、空、加载、错误、403 | P2 |
| /investigations/[id] | 调查详情 | 待完整盘点 | 正常、缺失、错误、403 | P2 |
| /analysis | 分析工作区 | 部分统一 | 正常、空、加载、错误、403 | P2 |
| /reports | 报告与导出 | 明显回归 | 正常、无报告、发布失败、403 | P0 |
| /statements | 财务报表 | 功能最完整但移动回归 | 正常、空、加载、错误、403 | P1 |
| /metric-library | 指标库 | 错误态不完整 | 正常、空、加载、错误、403 | P2 |
| /operations | 运行与发布 | 过渡状态 | 正常、空、失败、403 | P2 |
| /public | 公开财报模块 | 过渡状态 | 默认、入口不可用、403 | P3 |
| /internal | 内部经营分析模块 | 过渡状态 | 默认、入口不可用、403 | P3 |

每个路由至少在 1440px、1024px、390px 三个视口验收。不能仅凭正常态桌面截图判定完成。

---

## 3. 全页面一致性硬合同

页面被标记为“已迁移”前，必须同时满足：

1. 除 /login 外，页面由 page.tsx 层包裹 AppShell；内容组件不自带第二套导航。
2. 页面标题、说明、主操作、辅助操作的层级一致；错误态也保留页面身份。
3. 输入、选择、按钮、表格、提示、分页和加载反馈使用共享组件或批准的统一样式。
4. 正常、空、加载、错误、403 五类状态有一致语义，不直接向用户暴露未经转换的后端英文错误。
5. 所有关键数字、结论和导出结果按需要提供来源、期间、口径或证据入口。
6. 交互可由键盘完成；仅 hover 可见的核心信息不合格。
7. 主要触控目标不小于 44×44px；如视觉尺寸较小，必须扩大可点击区域。
8. 390px 视口不得产生页面级横向滚动；宽表必须在自身容器内滚动并有提示。
9. 不允许页面级行内样式复制设计令牌；例外须有注释和后续清理任务。
10. 组件测试、路由 E2E、视觉证据和 CI 必须来自同一提交。

---

## 4. 目标文件结构

以下为计划目标，不表示文件已经存在：

    apps/web/app/
      layout.tsx
      login/page.tsx
      globals.css
    apps/web/components/
      dashboard/app-shell.tsx
      dashboard/workflow-nav.tsx
      ui/button.tsx
      ui/input.tsx
      ui/select.tsx
      ui/field.tsx
      ui/alert.tsx
      ui/page-header.tsx
      ui/page-state.tsx
      ui/data-table.tsx
      ui/provenance-badge.tsx
      ui/skeleton.tsx
      ui/toast.tsx
    apps/web/e2e/
      navigation.spec.ts
      frontend-consistency.spec.ts
      frontend-states.spec.ts
      frontend-responsive.spec.ts
    apps/web/tests/
      dashboard-content.test.tsx
      shared-ui.test.tsx
      provenance-badge.test.tsx
    work/frontend-consistency/
      route-inventory.json
      screenshots/
      audit-summary.md

最终文件名可根据现有目录调整，但职责不得退回各页面自行实现。

---

## 5. 分阶段执行任务

### Task 0：冻结基线并建立失败门禁

**Files:**

- Modify: apps/web/tests/dashboard-content.test.tsx
- Modify: apps/web/e2e/navigation.spec.ts
- Create: apps/web/e2e/frontend-consistency.spec.ts
- Create: apps/web/e2e/frontend-responsive.spec.ts
- Create: work/frontend-consistency/route-inventory.json

**Step 1：保护并发改动**

记录 git status、当前 HEAD 和现有未提交文件所有者。若 dashboard-content.test.tsx 已被其他工作修改，先比较内容，禁止覆盖。

**Step 2：生成路由清单**

扫描 app 下 page.tsx，列出静态和动态交互路由，并对照 workflow-nav。把登录页明确列为唯一无 AppShell 路由。

**Step 3：先写失败门禁**

- 所有业务路由存在 AppShell；
- 错误态仍有页面标题；
- 390px 下 body 无横向溢出；
- 关键页面不出现浏览器默认样式的裸 input、select、button；
- 触控目标检查输出低于 44px 的元素清单。

**Step 4：运行并保存红灯证据**

    cd apps/web
    ./node_modules/.bin/vitest run tests/dashboard-content.test.tsx
    ./node_modules/.bin/playwright test e2e/frontend-consistency.spec.ts e2e/frontend-responsive.spec.ts

Expected: 现有缺陷对应的测试失败，失败项与 FE-01 至 FE-12 对应。

**Step 5：修正陈旧测试，不掩盖真实缺陷**

更新已获批准的导航文案断言；不得通过删除断言让测试变绿。

**完成标准：** 路由清单固定；每个 P0/P1 问题至少有一项可重复检测；基线结果归档。

---

### Task 1：P0 登录、退出与全局布局修复

**Files:**

- Modify: apps/web/app/login/page.tsx
- Modify: apps/web/app/layout.tsx
- Modify: apps/web/components/dashboard/app-shell.tsx
- Modify: apps/web/components/dashboard/workflow-nav.tsx
- Test: apps/web/tests/auth-shell.test.tsx
- Test: apps/web/e2e/frontend-consistency.spec.ts

**Step 1：为预期行为写失败测试**

- 登录页没有 AppShell，也没有孤立的全局退出入口；
- 登录表单使用统一 Field、Input、Button 和错误提示；
- 退出操作只出现在已认证的应用导航区域；
- 退出后跳转和焦点处理正确。

**Step 2：消除根布局中的认证 UI**

根布局只承担文档骨架、字体和全局 provider；认证动作由 AppShell 或专门的客户端边界承担。

**Step 3：迁移登录页**

删除重复行内样式，使用设计令牌和共享组件；保留清晰标签、校验信息、处理中状态和自动填充属性。

**Step 4：验证**

    cd apps/web
    ./node_modules/.bin/vitest run tests/auth-shell.test.tsx
    ./node_modules/.bin/playwright test e2e/frontend-consistency.spec.ts

**完成标准：** 登录与主应用属于同一视觉系统；退出入口位置唯一；无全局孤立页脚。

---

### Task 2：P0 Data 与 Reports 视觉回归修复

**Files:**

- Modify: apps/web/components/data/data-workbench.tsx
- Modify: apps/web/components/data/data-workbench.css
- Modify: apps/web/app/reports/page.tsx
- Modify: reports 页面关联组件与样式
- Test: 对应 Vitest 文件
- Test: apps/web/e2e/frontend-consistency.spec.ts

**Step 1：恢复可用性，不复活双重设计系统**

先把旧类名与现状逐项映射。选择“立即迁移到共享组件”或“暂时恢复必要旧样式”，但不能让无样式标记继续存在。

**Step 2：统一上传与映射流程**

上传区、阶段指示、字段映射、成功与失败反馈使用统一容器、按钮和提示；操作顺序和可用状态必须清楚。

**Step 3：统一报告页**

迁移选择器、按钮、报告卡片和状态反馈；将原始英文错误转换为中文用户提示，并保留可供排障的错误标识。

**Step 4：加删除顺序保护**

测试断言页面已经不依赖待删除类名后，才删除对应 CSS。提交中要能看出“迁移先于清理”。

**完成标准：** 两个页面无浏览器默认控件外观；正常、空、错误、403 均可辨识；测试与截图通过。

---

### Task 3：P1 统一页面状态与错误协议

**Files:**

- Create or Modify: apps/web/components/ui/page-state.tsx
- Create or Modify: apps/web/components/ui/alert.tsx
- Create or Modify: apps/web/components/ui/empty-guide.tsx
- Create or Modify: apps/web/lib/error-presentation.ts
- Modify: 所有业务页面的加载、空、错误和 403 分支
- Test: apps/web/tests/shared-ui.test.tsx
- Test: apps/web/e2e/frontend-states.spec.ts

**Step 1：定义状态协议**

统一 loading、empty、error、forbidden、not-found 的标题、说明、主操作、重试行为和诊断标识。

**Step 2：保留页面上下文**

状态页不能替换掉页面标题和导航。Metric Library 等页面即使失败也必须让用户知道自己所在位置。

**Step 3：集中转换错误**

禁止把 response 文本直接作为用户文案。保留 status、code、correlation id 供支持人员追查。

**Step 4：逐页接线**

按页面矩阵逐项实现，不接受只在共享组件故事页中通过。

**完成标准：** 同类状态跨页面文案、结构和操作一致；403 不再表现为普通系统崩溃。

---

### Task 4：P1 表格、表单与可追源组件收敛

**Files:**

- Modify: apps/web/components/ui/data-table.tsx
- Modify: apps/web/components/ui/provenance-badge.tsx
- Create or Modify: apps/web/components/ui/field.tsx
- Modify: Statements、Metric Library、Investigations、Reports 的相关组件
- Test: apps/web/tests/provenance-badge.test.tsx
- Test: apps/web/tests/shared-ui.test.tsx

**Step 1：补组件契约测试**

- 表格支持列标题、空态、窄屏容器滚动和键盘焦点；
- 字段包含可关联 label、帮助说明和错误信息；
- ProvenanceBadge 可点击或键盘打开，不依赖 hover；
- 来源入口能指向实际记录、证据或明确的来源详情。

**Step 2：迁移重复实现**

先迁移一页作为样板，验证后再扩展。禁止同名共享组件与页面私有组件长期并存。

**Step 3：保留财务可审计性**

高密度不等于隐藏上下文。金额、期间、币种、口径和证据字段按业务需要可见。

**完成标准：** 关键业务表格和字段遵循同一组件合同；来源信息支持鼠标、键盘和触控。

---

### Task 5：P1 响应式、触控与无障碍修复

**Files:**

- Modify: apps/web/app/globals.css
- Modify: apps/web/components/ui/button.tsx
- Modify: apps/web/components/dashboard/app-shell.tsx
- Modify: Statements 与其他宽表页面
- Modify: apps/web/e2e/frontend-responsive.spec.ts

**Step 1：把现有问题写成断言**

- 390px 下 documentElement.scrollWidth 不大于 clientWidth；
- 宽表只在局部容器滚动；
- 主交互点击区域至少 44×44px；
- Tab 顺序可预测，焦点可见；
- 仅 hover 的信息也可通过 focus/click 获取。

**Step 2：修复 Statements 599px 页面宽度**

定位固定宽度、min-width、grid 和 padding 来源。不得用全局 overflow-x: hidden 掩盖内容截断。

**Step 3：统一尺寸令牌**

视觉紧凑按钮可保留，但通过 padding 或伪元素满足触控区域；谨慎处理表格中的密集操作。

**Step 4：三视口回归**

在 1440、1024、390 三档对所有路由执行自动化检查并截图。

**完成标准：** 无页面级横向滚动；触控目标和焦点通过；桌面密度没有被移动修复破坏。

---

### Task 6：P2 Metric Library 与 Investigation 深度迁移

**Files:**

- Modify: Metric Library 页面、组件和样式
- Modify: Investigations 列表与详情页面、组件和样式
- Modify: 对应 Vitest 与 Playwright 文件

**Step 1：先定义业务信息层级**

指标库突出指标定义、公式、口径、适用范围、版本和来源；调查突出问题、证据、假设、结论、人工确认和状态。

**Step 2：迁移到共享组件**

表格、筛选、字段、标签、状态和证据入口不得再次复制私有实现。

**Step 3：处理动态路由**

调查详情纳入缺失、越权、加载和错误验收，不得只测列表。

**完成标准：** 两个专业模块保持高度可见的规则与证据，不因统一视觉而退化为普通卡片页。

---

### Task 7：P2 图表与服务端状态技术决策

**Files:**

- Modify: 2026-09-15 前端升级方案或新增 ADR
- Modify: package.json，仅在决策批准并有实际页面迁移时
- Modify: 相关页面与测试

**Step 1：用需求决定依赖**

TanStack Query 已安装但尚未形成使用模式；Recharts 尚未引入。先列出缓存、失效、轮询、错误恢复、无障碍图表和导出需求。

**Step 2：做最小样板**

仅选择一个真实页面验证收益、包体积、测试方式和失败降级。不得为了“技术栈看起来完整”全局替换。

**Step 3：形成裁决**

记录采用、暂缓或拒绝的理由，以及后续页面的标准模式。

**完成标准：** 每个新增依赖都有真实用途、测试和维护边界；没有半接入框架。

---

### Task 8：P3 Dashboard、Analysis、Operations、Public、Internal 收口

**Files:**

- Modify: 对应 app 页面和组件
- Modify: 页面相关测试
- Modify: apps/web/e2e/frontend-states.spec.ts

**Step 1：按角色使用页面模式**

- Dashboard：经营摘要与异常入口；
- Analysis：分析任务和证据工作区；
- Operations：发布、运行状态和失败恢复；
- Public：公开财报分析模块入口；
- Internal：内部月度财务经营分析工作台入口。

**Step 2：避免“统一即同质化”**

统一的是导航、状态、组件与交互规则，不是把五个页面做成相同卡片阵列。

**Step 3：完成状态矩阵**

逐页补齐正常、空、加载、错误、403，并在三视口验收。

**完成标准：** 所有导航入口达到同一完成度，同时保留两模块的清晰边界。

---

### Task 9：全链验收、证据归档与交付

**Files:**

- Modify: apps/web/e2e/navigation.spec.ts
- Modify: apps/web/e2e/frontend-consistency.spec.ts
- Modify: apps/web/e2e/frontend-states.spec.ts
- Modify: apps/web/e2e/frontend-responsive.spec.ts
- Create: work/frontend-consistency/audit-summary.md
- Create: work/frontend-consistency/screenshots/*
- Modify: docs/00_start_here/PROJECT_STATE.md，仅在全部验收通过后
- Modify: docs/50_plans/CURRENT_ROADMAP.md，仅由主协调者按正式状态更新

**Step 1：执行全量前端测试**

    cd apps/web
    ./node_modules/.bin/vitest run
    ./node_modules/.bin/tsc --noEmit
    ./node_modules/.bin/eslint .
    ./node_modules/.bin/playwright test

**Step 2：执行仓库门禁**

    cd ../..
    python3 scripts/check_docs.py --phase m1
    python3 scripts/check_docs.py --phase m6

**Step 3：生成视觉证据**

每个路由至少保存：

- desktop-normal；
- desktop-error 或 forbidden；
- mobile-normal；
- 该页面最重要的专业交互或证据状态。

截图必须标注 commit SHA、视口和状态，不接受来自不同提交的拼接证据。

**Step 4：人工走查**

主协调者按页面矩阵逐项确认：页面身份、主任务、反馈、数据可读性、来源、键盘、触控和移动布局。

**Step 5：更新状态**

只有全部硬门禁通过后，才更新 PROJECT_STATE 和 CURRENT_ROADMAP。任何剩余项必须写成明确缺口，不得用“基本完成”关闭。

**完成标准：** 同一 SHA 的自动化、截图、人工审查和 CI 全绿；页面矩阵无未裁决单元格。

---

## 6. 验收清单

### 6.1 功能与视觉

- [ ] /login 无 AppShell、无孤立退出入口，表单与主应用同一设计语言。
- [ ] 所有业务路由均有 AppShell 和正确导航分组。
- [ ] Data、Reports 不再出现浏览器默认控件或缺失样式。
- [ ] 所有页面在错误态仍保留页面标题与下一步操作。
- [ ] 403 使用统一权限说明，不显示原始英文后端响应。
- [ ] Provenance 可由点击、键盘和触控打开，并能到达真实来源。
- [ ] 390px 无页面级横向滚动。
- [ ] 关键触控目标达到 44×44px。
- [ ] 两模块保持产品边界，不退化为同构占位页。

### 6.2 自动化

- [ ] Vitest 全绿。
- [ ] TypeScript 检查全绿。
- [ ] ESLint 全绿。
- [ ] Playwright 导航、状态、一致性、响应式全绿。
- [ ] 文档 M1/M6 门禁全绿。
- [ ] GitHub CI 在同一提交全绿。

### 6.3 证据

- [ ] route-inventory.json 与实际路由一致。
- [ ] 三视口截图齐全并记录 SHA。
- [ ] audit-summary.md 逐项关闭 FE-01 至 FE-12。
- [ ] 没有把他人未提交文件带入交付。
- [ ] 提交已推送到 origin，最终回复包含提交哈希与验证结果。

---

## 7. Go / No-Go 规则

### 可以进入下一批次

- 当前批次测试全绿；
- 当前批次页面在三视口无新回归；
- 删除的旧 CSS 已有迁移证明；
- 新共享组件至少在真实页面使用，而非仅存在于组件目录；
- 当前分支与集成基线无未裁决冲突。

### 必须停止

- 工作区出现来源不明的未提交修改；
- 路由、权限或财务口径发生计划外变化；
- 为让测试通过而删除业务断言；
- 通过全局隐藏溢出、吞掉错误或伪造数据掩盖问题；
- 截图、测试与提交 SHA 不一致；
- CI 尚未完成却准备宣布“全部完成”。

---

## 8. 给接手 Agent 的启动指令

执行者收到启动授权后，应使用以下任务说明：

    读取 AGENTS.md、PROJECT_STATE、READING_ORDER、本计划和既有前端升级方案。
    先执行 Task 0，核对当前 HEAD 与未提交改动；不得覆盖他人文件。
    按 Task 0 到 Task 9 串行推进，每个任务遵循测试先行、最小实现、
    对应验证、范围检查、独立提交和推送。
    不得把计划项提前标成完成，不得先删除旧样式再迁移页面。
    每完成一个批次，报告路由覆盖、状态覆盖、三视口结果、测试、CI、
    提交哈希和残余风险。最终只有在同一 SHA 全部门禁通过后，
    才更新项目状态并申请关闭本计划。

---

## 9. 本计划的已知限制

- 本次浏览器环境中多个接口返回 403，未能观察所有页面的真实数据正常态；因此正式执行必须补充受控种子或合法测试身份。
- 本次诊断截图位于临时目录，不作为正式验收证据；Task 9 必须重新生成同一 SHA 的归档截图。
- 诊断时前端测试有一项陈旧导航断言失败；工作区随后出现该测试文件的并发修改，执行者必须先确认其归属和最终内容。
- 本计划不裁决新的产品功能，只修复与统一现有页面；若实施中发现功能需求变化，应另走产品决策流程。

---

Plan complete and saved to docs/superpowers/plans/2026-09-16-frontend-consistency-remediation-plan.md. Execution requires explicit user authorization and must follow the repository's current roadmap and closeout protocol.

---

## 10. 执行日志（滚动更新）

### 2026-09-17 P0 批次（诊断吸收 + Task 1/2/3 主体 + 新发现两项）

**对诊断的核对（HEAD 4c2e127，非诊断时的 ec6450a）：**
- FE-01/FE-02/FE-03/FE-04 属实并已修复（见下）；FE-06（390px 溢出）在当前
  HEAD 不复现——11 条路由 390×844 实测 body 宽全部 390，无横向溢出；
- FE-12（dashboard-content 旧导航断言）已由 b4ff5e7 修复；TanStack Query
  已由 06b893a 落地 statement-app 试点（诊断时点早于该提交）。

**新发现（比诊断更深的根因）：**
1. F2 批次（c84b006）声称落地的 token 定义从未入库：`--flow-space-1..6`、
   `--flow-radius-s/m/l`、`--flow-font-xs/s/m`、`--flow-error/-bg`、
   `--flow-info`、`--flow-shadow-card`、`--rep-line-3/4/5`、`--rep-slate`、
   `--rep-teal`、`--rep-ok-soft-2` 共 17 个 token 只被消费从未定义，
   flow-* 基础类与全部 Tailwind line-3/4/5 工具类静默失效。已在
   globals.css `:root` 补齐（monotone 线阶 + 与既有调色板同源刻度）。
2. F2 的「hex→var()」替换存在值漂移：dashboard `--green` 由 #075f45
   （对白字 6.8:1）误改为 var(--rep-teal)（#0d9488，3.05:1），trend 利润线
   与图例同病。已恢复 F2 前值；新增 `--rep-teal-strong: #0f766e` 供白字
   按钮使用（review 发布按钮 3.74:1 → 5.3:1）。

**本批落地：**
- Task 1：退出入口从根布局 footer 移入 AppShell 侧栏（showLogout prop，
  AUTH_TOKEN 门控）；登录页去内联样式（login.css，与主应用同一 token 源）。
- Task 2：恢复 data-workbench.css（阶段条/拖放区/清洗/发布分区）与
  reports-center.css（分区卡片/清单/表单区）；两页原生控件接入
  flow-btn/flow-btn--primary/flow-table/flow-error；ml-muted 跨页借用改
  reports-center__muted。
- Task 3：client.ts `request()` GET 失败改抛中文 FlowApiError（STATUS_TEXT
  映射 401/403/404/409/5xx），statement-app toMessage 统一
  「加载失败（状态码）：中文说明」。
- 守卫（对应 Task 0 的回归面）：tests/css-class-coverage.test.ts（tsx 内
  BEM `__` 类必须有 CSS 定义——本批即由其抓获两个额外死类
  investigation-head__text / ops-overview__muted，已补最小定义）；
  tests/auth-shell.test.tsx（退出入口唯一性 + 登录页禁行内样式 +
  根布局禁认证 UI）。
- FE-06 视口：11 路由 390px 溢出扫描通过（scripts 内一次性探针，未入库；
  Task 9 的 frontend-responsive.spec 待正式建）。

**验证：** 单测 76/76（+4 守卫）；statements e2e 4/4（含 axe 与重试流）；
dashboard 7/7（axe 898 违规归零，视觉基线 1440/1920 无需重录即通过）；
navigation/module-boundaries 16/16；investigation 4/4。user-closure 全量
本地复跑 1 失败（tests/integration/test_object_store.py MinIO
RequestTimeout），隔离复跑 0.47s 通过——负载性环境 flake，与前端改动无关。

**未完成（后续批次）：** Task 0 正式 e2e 门禁（frontend-consistency/
frontend-responsive.spec）、Task 4（ProvenanceBadge 键盘可达与原文跳转）、
Task 5（44px 触控目标）、Task 6-8（metric-library/operations/investigations
逐页迁移）、Task 9（状态×视口矩阵归档）。

### 2026-09-17 P1 批次（Task 0 e2e 门禁 + Task 4 可达性 + Task 5 触控目标 + FE-06 修正）

**对执行日志的重要更正**：前批「FE-06 在当前 HEAD 不复现」的结论是**假阴性**
——当时的探针跑在无真实数据的错误态上。本批把门禁改为生产构建（`next
build` + `next start`）后，真实数据下 /statements 在 390px 溢出至 599px、
/reports 552px、/metric-library 501px、/investigations 644px，诊断原始判
断正确。逐项修复：statements（stmt-sha SHA 长串 overflow-wrap）、reports
（freeze select 脱离固有宽度）、metric-library（列表轨道收窄、dt/dd 改
网格排布、ml-dep 去 nowrap、卡片脚注换行）、investigations（表格加
region+overflow-x 滚动容器）、全局（网格容器 minmax(0,1fr) 收轨模式）。
另删除 dashboard.css ≤760px 的旧版「横排 4 列 rail」规则——它与
AppShell 的 62px 竖轨在窄屏叠用，正是 413px 溢出的来源之一。

**本批落地：**
- Task 0：e2e/frontend-consistency.spec.ts（10 业务路由 AppShell+h1、
  /login 例外、/data /reports 样式回归探针）+ e2e/frontend-responsive.spec.ts
  （11 路由 390px 溢出 + 44px 触控目标 + 窄屏退出按钮可见性）；挂入
  test_module_boundaries_e2e.sh，且该脚本从 dev 改为**生产构建**——
  Turbopack dev 的 CSS 行为与生产不一致，按「dev 全绿≠生产正常」纪律收敛。
- Task 4：ProvenanceBadge 点击展开/收起（aria-expanded）+ group-focus-within
  键盘可达；数值单元格不加 tabIndex（避免一张表数百停止点），键盘路径=行级
  p{page} 徽标（组件注释已声明）。原文跳转仍待后端供稿决策（Task 9 前）。
- Task 5（首切片）：≤780px 下 flow-btn/flow-field 控件与登录表单 ≥44px；
  密集表格行级小按钮为密度设计的显式例外（spec 注释声明）。
- FE-04 收尾：≤1200px 侧栏 footer 只隐状态文案、退出按钮保持可见。

**验证：** 扩展后 module-boundaries 脚本 43/43（含 4 个新一致性测试 +
11 路由溢出门禁，生产构建）；单测 76/76；dashboard 7/7（视觉基线无变化）；
statements e2e 4/4；check_docs m6 PASS。

**未完成：** Task 6-8 逐页迁移（本批的溢出修复是止血，页面级 token/组件
迁移仍按计划推进）、Task 9 状态×视口矩阵归档、原文跳转后端供稿。

#### P1 补充（CI 首轮红灯修复）
module-boundaries-e2e 在 CI 的纯 web 栈（无 API）下暴露 /metric-library
错误态缺 h1（本地因 docker API 可达走了 loaded 态假绿，即 FE-10 原文）。
已修：loading/error 分支保留稳定「指标库」h1（ml-page-title）。43/43 复绿。

### 2026-09-17 P2 批次（review 吸收：数据态门禁、触控目标、溯源交互、lint 清零）

**review 核实结论**（HEAD 56be47d）：溢出四页表格、「测试未提交」「调试文件
存在」「metric-library 错误态缺 h1」均为过时快照（P1 已修复并 CI 绿）；
**属实并本批关闭**：lint 19 条警告、触控目标缺口（operations select
215×19、data 文件选择 192×21）、CI 门禁不含真实数据态、溯源卡 Escape/
外点关闭缺失。

**本批落地：**
- lint 19→1：清理全部未使用导入；保留 1 条 TanStack Table v8「incompatible
  library」编译提示为**登记例外**（v8 pin 的既定代价，阶段三评估升级）。
- 数据态门禁（阶段六切片）：frontend-responsive 新增「真实数据态」describe——
  路由拦截注入 statements 明细、metric-library、investigations、publishing
  快照固定数据，数据密集四页在 390px 的溢出门禁不再依赖环境是否有数据。
- 触控目标（FE-07 切片）：≤780px 下全站 select 与 input[type=file] ≥44px；
  门禁新增 operations select 与 data 文件选择的计算高度断言。
- 溯源交互（FE-08 切片）：Escape 关闭、点击外部关闭（pointerdown 监听）、
  组件测试 4 条（占位不伪造/aria-expanded 翻转/Escape/外点关闭）。真实来源
  链接仍待后端供稿决策（与浮层 pointer-events 联动，Task 9 前关闭）。
- h1 状态扫查：operations/investigations/analysis 页面头 h1 无条件渲染 ✓；
  dashboard 非 loaded 态由 dashboard-app 页头提供 h1 ✓（组件级扫查曾误加
  重复 h1，已撤销）。

**验证：** 单测 80/80（+4 溯源交互）；生产门禁 48/48（+5 数据态溢出 +
2 触控断言）；dashboard 7/7、statements 4/4、investigation 4/4；lint
0 error/1 登记例外；m6 PASS。

### 2026-09-17 P3 批次（Task 6-8 切片：PageState/表格职责/Operations-Investigations 迁移）

- **PageState 统一状态组件**（阶段四）：h1 稳定渲染（可选，页面已有无条件
  h1 时省略）、error/forbidden 用 role=alert、403 受控展示不裸抛技术串、
  恢复动作 = 重试（flow-btn--primary）+ 引导链接；operations-app 三分支
  已迁移，组件测试 4 条。
- **表格职责统一**（阶段五）：FlowDataTable 外层内建 overflow-x 滚动——
  任何使用方不再依赖页面自带 .stmt-table-wrap 之类的容器；investigations
  索引表从手写 table 迁入 FlowDataTable（排序/密度/局部滚动；进入调查
  链接可访问名不变，investigation e2e 4/4 佐证）。
- **Operations 控件迁移**（Task 8 切片）：冻结按钮 → flow-btn--primary、
  查看/下载链接 → flow-btn、错误块接 flow-error、label+select 包进
  flow-field（统一焦点态与 44px 触控目标）。
- **Task 9 切片**：溢出门禁扩到 1024/1440 两档视口 × 数据密集四页
  （路由拦截数据态）——门禁矩阵现覆盖 390/1024/1440。
- lint 维持 0 error / 1 登记例外（TanStack v8 编译提示）。

**验证：** 单测 84/84（+4 PageState）；生产门禁 56/56（+8 视口门禁）；
investigation 4/4、dashboard 7/7、statements 4/4；m6 PASS。

**未完成：** metric-library 全量迁移（761 行 ml-* CSS 的系统性收编）、
溯源真实来源链接（后端供稿决策）、Task 9 五态×三视口全矩阵归档截图。

### 2026-09-18 P4 批次（Task 6 主切片：metric-library 深度迁移）

- **状态外壳统一**：页面 loading/error（含覆盖矩阵区）从私有 ml-state 迁入
  共享 PageState（title="指标库" 保持 FE-10 的稳定 h1；覆盖区无 title 复用
  同一外壳）；ml-page-title/ml-state* 样式块删除。
- **控件与表格收编**：私有按钮样式 → flow-btn 变体（提交修订、治理
  创建草稿/激活/退役、修订开关，共 6 处）；私有 ml-table → 共享 flow-table
  （取数映射、分录模板、治理事件，共 3 处）。
- **token 系统性收编**：裸色值 63 → 7——页面级金棕警示对固化为文件作用域
  `--ml-warn-ink/-bg`（#805000/#fdf0dc，AA 对比注释；--rep-warn 对小字号
  软底不达标故不成全局替换）+ on-dark 白字 3 处（与 flow-btn--primary 同
  惯例）；删除自指 var 兼容块、未定义 token 消费（--rep-ink-soft、--ml-line）、
  无组件使用的 ml-header/ml-revise/ml-page-title 等孤儿块；871 → 780 行。
  剩余灰阶（#33465e/#8a97a8/#53647b 等）归并到 --rep-slate/--rep-muted
  （脚注文字对比度顺带提升）。

**验证：** 单测 86/86（含行业包 tab 2 条新测试）；lint 0 error/1 登记例外；
生产构建门禁 56/56（一致性 + 响应式 + 导航 + 边界）。教训复证：门禁前
必须按进程名 pkill 残留 next-server（`pkill -f next start` 杀不到改名的
next-server，5 个残留实例曾让首轮门禁跑 30 分钟不出结果）。

**未完成：** Task 6 另一半（investigations 详情页深度迁移）、Task 7 已由
F-Query/F-Charts 裁决覆盖、Task 8 其余页面切片、溯源真实来源链接（后端
供稿决策）、Task 9 五态×三视口全矩阵归档截图。
