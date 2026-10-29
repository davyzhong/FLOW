---
doc_id: FLOW-WI-VISUAL-LANGUAGE-20261024-001
title: 可复用视觉语言提炼与 FLOW 全项目视觉统一
doc_type: work-item
status: active
version: 2.8
created_at: 2026-10-24
updated_at: 2026-10-30
do_not_execute: false
owner: FLOW
depends_on: [FLOW-SPEC-VISUAL-LANGUAGE-20261024-001]
acceptance_refs: [FLOW-DECISION-D055]
applies_to: product-visual-language
decision_refs: [D052, D053, D054, D055]
supersedes: []
superseded_by: null
related_plan: ../../superpowers/specs/2026-10-24-flow-visual-language-system-design.md
confidentiality: project-internal
---

# 可复用视觉语言提炼与 FLOW 全项目视觉统一

## 2026-10-30 复工：概念图逐图视觉对齐

用户明确指出当前饼图、柱状图等图表的色系和视觉表达与 [A+C 概念板](../../assets/cockpit-visual-direction-2026-10-18.png) 有明显差距，要求接手此前 Agent 的全项目图形、图像、图表统一工作。PR #5、`bf98ed87` 的 token 色阶和截图是已完成基线，不能据其历史结案状态宣称当前视觉目标达成。唯一执行项仍为路线图事项 12；K3 全量知识整理已被用户取消，不读取全量知识库。

**当前审查所见。** 概念板使用暖纸白画布、深墨蓝结构、有限古金、翡翠绿和中性灰；趋势线以墨蓝/古金为主，瀑布正向为绿、负向为低饱和冷色，堆叠构成使用墨蓝/绿/金/灰。2026-10-29 已提交的驾驶舱与费用页截图虽接入相近 token，但费用环图/分组柱仍出现大面积金色及第四种明亮蓝，图例、柱宽、环宽、网格与概念板不完全一致；总览图表区比概念板更拥挤，信息层级与移动端需实测。先对照真实页面再改，不以单次色板替换视为完成。

**串行实施与验收。**

1. 盘点项目内全部当前用户可见图表与其他图像表达（ECharts、手绘 SVG、KPI 微图、图谱、报告/离线图形、README 当前截图），逐对象记录使用的颜色、字体、形态、语义色边界、概念板对应表达和差距；不读取知识库原文。
2. 先修共享视觉语言 token 和图表构建器，再逐页修例外；系列色采用概念板的墨蓝、古金、翡翠绿、中性灰层级，正负/风险语义色保持正确。通过图例、明暗、线型和标签区分，不为贴图而伪造数据。
3. 在隔离演示数据下复采全部适用页面的桌面/平板/手机截图，重点逐张目检饼图、环图、柱图、堆叠图、趋势、瀑布、杜邦、KPI 微图和来源表达；报告与离线输出按同一语义复验。差距报告逐对象标注已修正、受数据限制或不适用，并附代码 SHA、视口与数据批次。
4. 运行 token 生成一致性、相关前后端测试、类型检查/构建、文档 M1/M6、链接、视觉矩阵和必要的可访问性验证；独立复核影响既定需求的缺口，准确 SHA 的 CI 结果核验后才重新结案。

**边界。** 历史截图和原始档案保留；运行数据、指标值、计算口径和来源不为视觉外观改写；不修改 K3、ObsidianWiki 或知识发布版本。工作包旧的「已完成」记录仅代表 2026-10-26 阶段，不代表此次复工验收。

## 目标

从已确认的 A「高管编辑部」+ C「财务报告画布」概念图中提炼跨项目可复用的视觉语言；将这套语言应用到 FLOW 全部产品页面、图表、报告/离线输出及当前用户可见的 README 视觉材料；校准当前有效文档，使其准确描述已完成的 7a 原型及本任务的真实状态。

## 当前实施记录（2026-10-24）

- **2026-10-25 图表明细表语义补齐（准确 SHA `01e8e25dd426ed43ad6a2cad76544bbbe623eb99`）：** DOM 盘点发现 `/cockpit` 的经营趋势、现金变动桥、期间费用三张同值明细表没有无障碍名称；现为三表补充语义标签及组件回归断言。定向组件测试 2/2、Web typecheck、production build 通过；以该 SHA 重采 20 路由×3 视口 60/60 ready、零页面/API/浏览器错误、外部请求和横向溢出；Axe 桌面 20 路由零违规。其余图表的值/来源/交互审计仍继续。

- **2026-10-25 全路由最终截图复核（代码 SHA `01e8e25dd426ed43ad6a2cad76544bbbe623eb99`）：** 20 路由×3 视口 60/60 内容就绪，页面/API/浏览器错误、外部请求、横向溢出均为 0；Axe 4.13 桌面 20 路由零违规。人工复核全部 20 张桌面截图，确认功能范围较窄页面留白与当前真实功能/隔离样本相符，不用虚构内容填充；未发现需代码修正的 P1/P2。原生浏览器 200% 缩放仍无法由受控 API 设置，标为未直接验收；390/360 CSS px 仅作为窄视口补充证据。当前证据和限制已同步覆盖报告、README、项目状态、交接与路线图。下一步按序完成剩余图表语义及复杂交互态核对，再做独立复核与准确 SHA CI。

- **2026-10-25 导出与打印视觉核验（代码 SHA `d554bc317e8c948d776833b9868cdce4a9dd4c81`）：** 统一 operations、冻结客观报告、通用出版 HTML/PDF 与离线驾驶舱的纸白/墨蓝/古金 token、衬线标题、数字字体和打印页式；PPTX 添加纸面背景/金色识别线并按平台映射中文字体；XLSX 统一表头、斑马纹、A4/分页/筛选冻结和宽表 fit-to-width，修复默认证据列未自适应导致打印内容挤在窄栏的问题。同步将 PDF 数字族、报告利润图强调色、环图文字与现金流零轴接入 token。使用隔离 synthetic 样例检查 HTML、Chromium PDF、PPTX Quick Look、XLSX A4 打印预览；未把样例输出提交为业务数据。定向 API 测试 27/27、Ruff、视觉 token 生成器 `--check`、离线 CSS token unittest、`git diff --check` 通过；独立复核无 P1/P2。离线总览已按此 SHA 重生成，批次 `01a16e5a-7c2c-79ab-9608-522ba64cce88`、manifest SHA `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`。原生浏览器 200% 缩放仍未直接验收，浏览器快捷键无效且当前自动化不能操作 Edge 工具栏；不能以 390 CSS px 重排代替。下一子步为全路由最终差距复核和最终矩阵，不结案、不启动 K2。

- **2026-10-25 交互与键盘增量（代码 SHA `52418d88c9338b41c59f14f3d699d758c36bf8a1`）：** 全站跳过导航入口及主内容键盘焦点已接入；19/19 AppShell 路由首 Tab/Enter 导航通过。依赖图修复重复 metric_code 节点身份、边端点、图层切换残留选择和窄屏阅读；常用/全部/专业层分别 32/13、65/28、33/7 个节点/边，零重复 ID，边路径正常。重复编码深链按 collection 正确定位。390 CSS px 页面无溢出，图谱可横向滚动并键盘阅读。Web 测试 38 文件/209 项、typecheck、production build 通过；lint 0 错误/4 条既有警告；独立复核无 P1/P2。精确 SHA 下矩阵 60/60 ready，Axe 桌面 20 路由零违规。受控 CLI 无法直接设置浏览器原生 200% 缩放；窄屏重排只作为补充证据，原生缩放保留未验收。下一子步是 HTML/PDF/PPTX/XLSX 模板与打印，不结案、不启动 K2。

- **2026-10-25 图表首轮语义审计（代码 SHA `1f75792a103af0cbe0d6b483316a26cc958fe391`）：** 复核全路由 34 个可视对象和代表性 API 序列；补齐图表 aria 名称中的期间/单位，批次状态及版本图表配套同源明细，亏损瀑布总计按负向语义色显示，并修复盈利能力图合法 0 值误作缺失的问题。Web 38 文件/205 项测试、typecheck、生产 build 通过，lint 0 错误/4 警告；独立终审无 P1/P2。该 SHA 的 20 路由×3 视口 60/60 ready，Axe 20 个桌面路由零违规，截图与结果 JSON 均绑定该 SHA；对应 run 在后续文档提交时被替代，最终 CI 以当前 HEAD 的 Actions 状态为准。下一步继续完整键盘/交互态、真实 200% 缩放，以及 HTML/PDF/PPTX/XLSX 模板和打印验收。本轮没有结案工作包。

- **2026-10-25 前一代码阶段记录（准确代码 SHA `b04a7c5425c340681828f1c15c15f3071b1e2782`）：** 修复瀑布图只含负 `total` 时纵轴漏算 `hi` 端点导致的画布裁切；负值范围现按所有柱的 `lo/hi` 端点计算，负 delta 连接线锚定变动前累计值，负值标签绘制在柱下方。新增负利润与仅负总计回归用例，相关 4 个测试文件 33/33、Web typecheck、视觉 token 检查和 `git diff --check` 通过，独立代码复核无 P1/P2。精确 SHA 下矩阵 60/60 ready，浏览器/API 错误、外部请求、横向溢出为 0；Axe 4.13 桌面 20 路由零违规，截图及 JSON 均绑定此 SHA。GitHub Actions run `40199235605` 正在运行，最终状态须以该 SHA 对应结果为准。此修复只关闭负值瀑布图绘制缺陷；图表逐对象事实/单位/期间/来源审查、交互/键盘、真实 200% 缩放和四类输出模板/打印仍未验收。

- **2026-10-25 历史状态（准确代码 SHA `0b06d01c07bf7e7c12e1565a17bce2b94c83aa04`）：** 报告中心编辑式双栏/窄屏单栏和指标库桌面双列卡片已完成；报告中心组件 12/12、指标库定向测试 16/16、Web typecheck、production build 通过。20 路由×3 视口矩阵 60/60 ready、页面/API/浏览器错误、外部请求、横向溢出为 0；Axe 4.13 桌面 20 路由零违规。远端 CI 状态按当前 HEAD 精确 SHA 实时查询；文档快照不代替 GitHub Actions 状态。当前本地没有浏览器验收脚本运行；下一步从逐图表事实/单位/期间/图例/来源/同值表达审查继续，再完成交互/键盘、真实 200% 缩放和四种导出/打印。Axe 整改已完成，不再列为待办。

- 2026-10-25（代码 SHA `2abdad9621ab03141beb3ceb5e0da64f3d636cba`）：报告中心桌面改为双栏编辑式卡片，使用概念板的衬线主标题、古金眉线和纸面分区，窄屏回到单栏；报告数据和操作逻辑不变。报告中心组件 12/12、Web typecheck、production build 通过。新增可复跑矩阵脚本 `scripts/capture_visual_language_matrix.mjs`；当前 20 路由×3 视口 60/60 内容就绪，页面/API 错误、外部请求、横向溢出均为 0。Axe 4.13 桌面 20 路由零违规。当时 SHA 的 PR CI run `40195231596` 已由后续代码 SHA `0b06d01c` 的 run `40195845311` 接替；当前状态见本节最新记录。图表事实逐项复核、完整交互、实际 200% 浏览器缩放以及 HTML/PDF/PPTX/XLSX 版式与打印仍未验收。

- 2026-10-25（代码 SHA `cc0fb2eff5d7dbb01f48fda3e84c8c23c9e35583`）：财报页利润瀑布、现金桥、资产/资本结构、现金流比较图新增同值折叠表；原图表标签与数据口径保持不变，移动端可聚焦横向阅读。财报组件 8/8、前端 201/201、typecheck、production build 通过。更新后的 20×3 路由矩阵 60/60 ready，Axe 4.13 桌面 20 路由零违规，指标依赖图交互无错误；矩阵及逐路由 Axe JSON 均绑定此 SHA。仍待图表期间/单位/来源逐对象审计、复杂交互状态和四类导出打印验收。

- 2026-10-25（代码 SHA `3e8a1676f79e0e7c350cd950326ac2128c08ddc7`）：全站对比度/结构修复已提交推送；Web typecheck、37 文件 201/201 单测、Next.js production build、token 生成检查、M1 和 diff-check 通过。Axe 4.13 对 20 个桌面路由为零违规；20×3 截图矩阵 60/60 ready，错误/外部请求/溢出为零；360 CSS px 的 20 路由首 Tab 焦点可见且零溢出。独立输出矩阵和限制见[覆盖验收](../../60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md)。图表逐对象语义、导入/筛选/报告交互和四类导出打印验收仍未完成。

- 已建立 `packages/flow-visual-language/`，包含 `tokens.json` 单一源、生成 CSS、表达范式、无业务事实样例；生成器同时输出 TypeScript/Python token 映射。
- 已接入 Web 全局主题、共享导航、主要 cockpit/data/analysis/operations 样式、ECharts/SVG 财务图色板与离线驾驶舱预览。报表 Matplotlib 图表读取同一 token 映射；HTML/PDF、PPTX、XLSX 主要渲染器已接入主题映射。代表性 HTML/PDF/PPTX/XLSX 输出和打印核验已于 2026-10-25 完成（代码 SHA `d554bc317e8c948d776833b9868cdce4a9dd4c81`，27 项定向后端测试通过）；原生 200% 阅读仍无法直接验收；最终矩阵与桌面视觉总览已按 SHA `32e4b08fb2fddc0ad424a5ac3bb5d8cc519414c4` 完成。剩余为图表语义与复杂交互态核对、独立复核及准确 SHA CI。
- Web typecheck 通过；前端 37 个测试文件、201 项通过；调查表和全局原生表单控件视觉调整后，typecheck、全量 201 项前端测试及 Next.js production build 通过。视觉 token `--check` 和 `git diff --check` 通过。
- 2026-10-25：提交 `9cf65f6d58e0cdb33d8e04c17d843a8c9bbc1489` 下重采 20 路由×3 视口，60/60 内容就绪、API/浏览器错误/横向溢出/外部请求均为 0；60 张截图与 supplemental 引用已同步到覆盖报告。调查表按纸面风格修正，所有原生单选/复选控件改用古金品牌色。此轮截图矩阵关闭了默认视图加载和版面边界验收；最终视觉整改后仍需更新截图，逐图表、交互、无障碍和输出模板仍待验收。PR #5 的 dashboard 视觉回归暴露 Linux/macOS 两套截图基线都滞后于当前纸白/海军蓝主题与仪表盘版式。核对 CI 实际截图后确认这是已批准视觉更新，不是页面故障；更新 Linux 与 macOS 两组平台基线。隔离临时 Postgres/Redis/MinIO Compose 项目上，`scripts/test_dashboard.sh` 连续两次 7/7 通过，第二次为不更新快照的验收；同轮报告渲染器定向测试 21/21 通过。临时容器、专属数据库卷与 Compose 网络已清理。Linux 基线更新后的准确 SHA 全量 PR CI 尚待完成；此记录不代表视觉工作包完成。
- Playwright 截图覆盖 20 路由×3 视口；修复 `/operations` 报告查询 UUID 参数类型后，代码 SHA `9cf65f6d` 下最新矩阵重采，60/60 HTTP 200、内容就绪、API/浏览器错误、外部请求、横向溢出均为零；指标依赖图交互截图也在同一 SHA 重采。热力图渐变、财报分组柱与瀑布图已接入语义 token。20 张桌面图审阅后已调整共享链接/控件色、指标库古金强调线、模块落地页衬线标题/卡片节奏和财报页品牌强调色；红色财务负值语义保持不变。指标依赖图默认聚焦“常用”层，并保留“全部/专业”范围切换；图谱画布按当前节点层高度展开，默认截图 31 个节点可见、零错误；“全部”视图的高密度缩放仍待核。视觉差异与剩余顺序见[视觉覆盖验收](../../60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md#20-路由截图首轮差异盘点2026-10-24)：驾驶舱、财务出版页和数据工作台较接近；分析及功能范围较窄的页面仍有自然留白；逐图表、报告模板/打印、图表辅助表达、导入/映射与筛选交互、键盘焦点及对比度尚未验收。
- 2026-10-25：在 `9cf65f6d` 阶段基线上对 20 个默认桌面路由运行 Axe，发现 359 个色彩对比节点、7 个驾驶舱子页缺少 H1、1 个不可聚焦滚动区，以及调查详情的定义列表/landmark 语义问题。已在 `3e8a1676` 完成全站对比度与结构整改；准确结果为 Axe 4.13 桌面 20 路由零违规，且 20×3 矩阵为 60/60 ready。因此这项整改已关闭。后续顺序为：逐图表/数据表达核对 → 交互/键盘/200% 阅读 → HTML/PDF/PPTX/XLSX 版式与打印核验 → 最终矩阵和独立复核。
- 截图与逐路由结果在 [视觉覆盖验收](../../60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md)；synthetic manifest SHA 为 `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`，数据库只位于 `/tmp/flow-visual-audit-20261024`。
- 尚待完成的当前验收：逐页复核剩余概念板差异；逐图表核对期间、单位、图例、事实类型、来源与同值表达；验证导入/筛选/报告空错状态；原生浏览器 200% 阅读直接验收（当前浏览器自动化不能操作 Edge 工具栏，390 CSS px 重排仅为补充证据）；最终代码 SHA 下重采矩阵；完成最终独立复核及准确 SHA CI。HTML/PDF/PPTX/XLSX 代表性模板与打印核验已在 `d554bc317e8c948d776833b9868cdce4a9dd4c81` 完成，后端定向测试 27/27、Ruff、token 检查通过。图谱层级、重复编码深链、19 个 AppShell 路由键盘导航已在代码 SHA `52418d88` 下验收；目录中的当前 20×3 矩阵和 Axe 结果仍绑定 `52418d88c9338b41c59f14f3d699d758c36bf8a1`，最终视觉收敛后须再重采。阶段矩阵只证明其对应 SHA 的默认态。

## 依赖与执行门

- 唯一范围与验收定义见[视觉语言设计规格](../../superpowers/specs/2026-10-24-flow-visual-language-system-design.md)。本工作包落实路线图事项 12；规格/工作包获用户确认前不进入产品实现。
- 当前项已由用户选择插入 K2 前，位于唯一主线队列队首；用户已批准设计规格与工作包，可开始实施。
- 实施始终串行推进；路线图是唯一 To-do。此工作包提供范围与验收，不另建可独立领取的任务清单。
- 视觉概念板是风格参考，不是数据来源。真实披露、模拟数据、预测、缺失和降级状态须保留各自事实标签；不生成伪指标或装饰性假数据。
- 全部浏览器截图和数据相关检查使用临时隔离数据目录；不连接或恢复常驻库，不修改用户目录中的 `/Users/qiming/.flow/flow.sqlite3`，不触碰其他 worktree 内的用户修改。

## 串行实施顺序与文件映射

以下阶段是此工作包内的执行次序，不是独立 To-do；始终只有 CURRENT_ROADMAP 中的本事项可领取。

### 可复制视觉语言资产与 token 流程

- 在 `packages/flow-visual-language/` 建立带目录约定的资产包：`README.md`（结构、版本与跨项目复制说明）、`tokens.json`（唯一源）、`tokens.css`（可直接复制的 Web tokens）、`patterns.md`（版式/图表范式）、`specimen.html`（不含财务事实的离线样式样例）。
- 编写 `scripts/build_flow_visual_language.py`，仅用 Python 标准库从 `tokens.json` 生成 CSS、TypeScript 消费映射和 Python 报告主题映射；`--check` 比较工作树文件与生成结果，防止多份颜色/字体真相漂移。
- 建立 `apps/web/lib/visual-tokens.generated.ts` 和 `services/api/src/flow_api/visual_tokens.py` 作为生成目标。非 Web 项目可直接复制 JSON/CSS 与模式手册；不发布 npm 包或安装运行时依赖。

### Web 基础主题与共享外壳

- 先改 `apps/web/app/globals.css`、`apps/web/components/shell/app-shell.css`、`apps/web/app/login/login.css`，以 tokens 统一纸白背景、海军蓝外壳、古金强调、衬线标题/无衬线正文和数字样式。
- 用 `apps/web/components/modules/module-landing.css` 与共享 UI 样式核对表面、控件、卡片、边框、焦点态和语义状态；保留登录页不包 AppShell 的路由规则。

### 全路由页面与全部图表

- 按现有页面边界逐页改造，不重排无关业务流程：`cockpit/cockpit.css`、`dashboard/dashboard.css`、`data/data-workbench.css`、`analysis/four-question-workbench.css`、`investigation/investigation.css`、`investigation/investigations-index.css`、`metric-library/metric-library.css`、`operations/operations-overview.css`、`operations/operations.css`、`reports/reports-center.css`、`statements/statements.css`，以及实际存在的 page/component 样式文件。
- 在所有 20 个路由逐个检查导航/页眉、核心结论、筛选、内容密度、表格、来源、空错加载降级态；对登录、内部、公开、动态调查详情保留各自任务结构。
- 统一图表系列、坐标、提示框、标题、图例与同值表样式：`cockpit/charts/echarts-base.tsx`、`cockpit/charts/builders.ts`、`cockpit/charts/module-options.ts`、驾驶舱可视化组件，以及 `statements/charts/{donut-chart,grouped-bar-chart,kpi-cards,waterfall-chart}.tsx`。

### 报告/出版与离线输出

- 用同一 token 语义校准 `services/api/src/flow_api/publishing/renderers.py`、`operations/renderers.py`、`statements/objective_report_html.py`、`statements/objective_report_charts.py`、`statements/objective_report_pdf.py` 中的 HTML/PDF/PPTX/XLSX 视觉映射。
- 调整 `scripts/export_cockpit_snapshot.mjs` 生成的离线页面结构/样式引用；不要编辑由它生成的当前预览 HTML 作为源文件，也不启动 GitHub 自动截图工作流。

### 全量差距验收与文档同步

- 以 `docs/60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md` 记录 20 路由 × 3 视口、逐图表/表达状态、代码 SHA、隔离批次 manifest SHA 和采集限制；截图放入该报告索引的专属目录。
- 同步本工作包“当前成果与限制”及 README、状态、交接、规格、页面/报告/截图索引；旧 7a 与历史截图内容保留为注明版本/日期的历史证据。
- 最终运行 generator `--check`、Web 相关单元测试/typecheck/build、报告渲染器定向测试、隔离数据的 20 路由三视口浏览器验收、M1/M6、计划视图、链接与 diff 检查；随后由独立上下文复核。

## 范围

### 可复用视觉语言

交付能从 FLOW 仓库独立复制的 `FLOW Visual Language` 规范资产，包括：

- 视觉原则、颜色和状态语义、中文字体组合、数字/单位排版、间距/边界/层次、响应式规则、可访问性与反模式。
- 具有稳定语义名称的 token 定义和可复制的 CSS token 文件；CSS 文件及随附说明可被其他 Web 项目直接采用，其余技术栈可依语义 token 映射。
- 页面与图表表达范式：编辑部页眉、核心指标、趋势对比、利润/现金变动桥、杜邦/结构拆解、洞察/行动、来源/口径面板、数据表与移动端阅读流。
- 明确概念图的适用边界：复用信息层级与构图，不复用其示意数值、企业事实、判断或无法追源的阈值。

### FLOW 产品视觉表面

- 覆盖 `apps/web/app` 全部 20 个页面路由，含登录页和动态调查详情；按页面任务复用一致语言，不强制改成相同布局。
- 覆盖所有可见图表、数据表达、筛选器、表格、空/错/加载/降级态、导航、抽屉及来源/口径区。
- 覆盖报告/出版渲染的 HTML、PDF、PPTX、XLSX，以及本机离线总览与预览包。XLSX 优先保证数字表达、筛选、复制和审计，不添加不适用的装饰图。
- 覆盖 README 产品截图、导览、架构/流程图和截图说明；按需校正相关的产品说明、运行与设计文档。

### 当前文档与项目状态

- 全面检索当前有效文档中关于页面、图表、报告、视觉规范、截图来源和本机运行方式的说明；修正与实际实现不符的内容。
- 同步 `README.md`、`docs/README.md`、`docs/00_start_here/PROJECT_STATE.md`、`docs/00_start_here/READING_ORDER.md`、`HANDOFF.md`、`docs/50_plans/CURRENT_ROADMAP.md`、`docs/50_plans/README.md`、新增工作包/设计规格、生成式计划状态视图、截图索引及被实现直接影响的产品/架构文档。
- 历史归档、原始资料、不可变档案、旧验收记录和旧截图不覆写；其中的旧状态继续标作历史，不得作为当前入口或当前验收依据。

## 验收

### 视觉语言资产

- 在仓库中有唯一规范入口、一个可复制的 token/CSS 来源和表达范式手册；语义命名足以映射到 React/CSS、图表和报告导出，不需要外部服务或新增运行时依赖。
- 颜色对比、正负/警告/中性色语义、字体回退、数值对齐、表格和图表颜色规则明确；在明暗/彩色打印和窄屏条件下不丢失关键信息。
- 至少包含一个无业务数据的样式范例，用于在其他页面/项目验证 typography、表面、指标卡、图表、来源面板和行动卡的组合。

### 页面与表达矩阵

- 20/20 路由和其中每个图表/数据表达均登记桌面 1440、平板 1024、手机 390 的检查结果，状态为符合、已调整、数据受限或不适用；动态详情通过隔离 Finding 进入。
- 全部路由无浏览器错误和页面级横向溢出；键盘可操作、焦点可见、放大阅读和颜色对比检查通过；图表均有可访问的标题/说明和同值数据表或等价的非画布表达。
- 每个图表的期间、单位、图例、事实类别和来源边界准确；已有图保持正确计算和可追溯行为，缺少数据的场景继续显式说明缺口。
- HTML/PDF/PPTX/XLSX 视觉语义可相互对应。对固定格式的可读性和打印方式单独核验，不要求像素级一致。
- 前后截图矩阵关联代码 SHA、隔离演示批次/manifest SHA 和视口；输出只放在已索引的视觉验收目录，不启动 GitHub 截图自动化。

### 文档、验证与集成

- 当前有效文档中不再出现“7a 正在进行/待验收”等现况描述；已完成 7a 的合并 SHA/run 与限制准确，新的队列计数、唯一队首和下一动作一致。
- 对被改动的有效文档执行 M1、M6、计划视图和链接检查；README 相对链接零断链，差异无空白错误。
- 对被改动代码执行相关组件/E2E/报告渲染器验证、Web typecheck 和 production build；以隔离演示数据完成三视口全路由验收。
- 最终交付由未参与实现的独立上下文只读复核，只对正确性或需求 P1/P2 缺口回修；记录最终 merge SHA 与其自身 CI 结果。

## 明确限制

- 视觉相似度不覆盖真实数据完整性；账龄独立真实切片、真实企业周期、公开财报 C 级和其他长期路线图目标依旧受各自门禁约束。
- 不更改 CI/CD 配置、数据库 schema/migration、部署发布流程；不删除历史材料，不恢复截图工作流。
- 已完成 D055/7a 工作包保持 completed；本工作包是在原型交付后的视觉语言产品化与全项目统一，不重新打开或改写 7a 的历史验收结论。


## 2026-10-26 结案

- 可复用视觉语言资产及全项目视觉收敛已完成：20 个路由、图表同值表达、键盘/交互、HTML/PDF/PPTX/XLSX 代表性输出版式、离线快照、README 视觉材料均有实施和验收证据。
- 本轮最终隔离验收：synthetic manifest `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`；`verify_damai_demo` 19/19；可见性矩阵 164/164（154 HTTP 200、10 预期拒绝、0 失败）；Playwright 17/17。应用截图矩阵 SHA `01e8e25dd426ed43ad6a2cad76544bbbe623eb99` 为 20 路由×3 视口 60/60，Axe 桌面 20 路由零违规。最后的 E2E 选择器修正提交 `d01daa11`，独立复核无 P1/P2，`git diff --check` 通过。
- **外部条件受限项：** 原生浏览器 200% 缩放未直接验收。Mac 锁屏导致无法操作本机 Edge 工具栏，受控浏览器 API 也不提供该控件；390/360 CSS px 响应式检查不等价。可完成部分已用响应式矩阵、键盘和 Axe 证据验收。恢复条件：设备解锁且可直接设置原生缩放的自动化/人工浏览器可用时，补做原生 200% 核验并追加记录。
- 独立代码复核未发现影响正确性或既定需求的 P1/P2。
- 视觉包结案后按唯一队列启动 K 轨 K3；此包不再执行。
