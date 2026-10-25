---
doc_id: FLOW-WI-VISUAL-LANGUAGE-20261024-001
title: 可复用视觉语言提炼与 FLOW 全项目视觉统一
doc_type: work-item
status: active
version: 2.0
created_at: 2026-10-24
updated_at: 2026-10-25
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

## 目标

从已确认的 A「高管编辑部」+ C「财务报告画布」概念图中提炼跨项目可复用的视觉语言；将这套语言应用到 FLOW 全部产品页面、图表、报告/离线输出及当前用户可见的 README 视觉材料；校准当前有效文档，使其准确描述已完成的 7a 原型及本任务的真实状态。

## 当前实施记录（2026-10-24）

- **2026-10-25 最新增量（准确代码 SHA `b04a7c5425c340681828f1c15c15f3071b1e2782`）：** 修复瀑布图只含负 `total` 时纵轴漏算 `hi` 端点导致的画布裁切；负值范围现按所有柱的 `lo/hi` 端点计算，负 delta 连接线锚定变动前累计值，负值标签绘制在柱下方。新增负利润与仅负总计回归用例，相关 4 个测试文件 33/33、Web typecheck、视觉 token 检查和 `git diff --check` 通过，独立代码复核无 P1/P2。精确 SHA 下矩阵 60/60 ready，浏览器/API 错误、外部请求、横向溢出为 0；Axe 4.13 桌面 20 路由零违规，截图及 JSON 均绑定此 SHA。GitHub Actions run `40199235605` 正在运行，最终状态须以该 SHA 对应结果为准。此修复只关闭负值瀑布图绘制缺陷；图表逐对象事实/单位/期间/来源审查、交互/键盘、真实 200% 缩放和四类输出模板/打印仍未验收。

- **2026-10-25 当前状态（准确代码 SHA `0b06d01c07bf7e7c12e1565a17bce2b94c83aa04`）：** 报告中心编辑式双栏/窄屏单栏和指标库桌面双列卡片已完成；报告中心组件 12/12、指标库定向测试 16/16、Web typecheck、production build 通过。20 路由×3 视口矩阵 60/60 ready、页面/API/浏览器错误、外部请求、横向溢出为 0；Axe 4.13 桌面 20 路由零违规。远端 CI 状态按当前 HEAD 精确 SHA 实时查询；文档快照不代替 GitHub Actions 状态。当前本地没有浏览器验收脚本运行；下一步从逐图表事实/单位/期间/图例/来源/同值表达审查继续，再完成交互/键盘、真实 200% 缩放和四种导出/打印。Axe 整改已完成，不再列为待办。

- 2026-10-25（代码 SHA `2abdad9621ab03141beb3ceb5e0da64f3d636cba`）：报告中心桌面改为双栏编辑式卡片，使用概念板的衬线主标题、古金眉线和纸面分区，窄屏回到单栏；报告数据和操作逻辑不变。报告中心组件 12/12、Web typecheck、production build 通过。新增可复跑矩阵脚本 `scripts/capture_visual_language_matrix.mjs`；当前 20 路由×3 视口 60/60 内容就绪，页面/API 错误、外部请求、横向溢出均为 0。Axe 4.13 桌面 20 路由零违规。当时 SHA 的 PR CI run `40195231596` 已由后续代码 SHA `0b06d01c` 的 run `40195845311` 接替；当前状态见本节最新记录。图表事实逐项复核、完整交互、实际 200% 浏览器缩放以及 HTML/PDF/PPTX/XLSX 版式与打印仍未验收。

- 2026-10-25（代码 SHA `cc0fb2eff5d7dbb01f48fda3e84c8c23c9e35583`）：财报页利润瀑布、现金桥、资产/资本结构、现金流比较图新增同值折叠表；原图表标签与数据口径保持不变，移动端可聚焦横向阅读。财报组件 8/8、前端 201/201、typecheck、production build 通过。更新后的 20×3 路由矩阵 60/60 ready，Axe 4.13 桌面 20 路由零违规，指标依赖图交互无错误；矩阵及逐路由 Axe JSON 均绑定此 SHA。仍待图表期间/单位/来源逐对象审计、复杂交互状态和四类导出打印验收。

- 2026-10-25（代码 SHA `3e8a1676f79e0e7c350cd950326ac2128c08ddc7`）：全站对比度/结构修复已提交推送；Web typecheck、37 文件 201/201 单测、Next.js production build、token 生成检查、M1 和 diff-check 通过。Axe 4.13 对 20 个桌面路由为零违规；20×3 截图矩阵 60/60 ready，错误/外部请求/溢出为零；360 CSS px 的 20 路由首 Tab 焦点可见且零溢出。独立输出矩阵和限制见[覆盖验收](../../60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md)。图表逐对象语义、导入/筛选/报告交互和四类导出打印验收仍未完成。

- 已建立 `packages/flow-visual-language/`，包含 `tokens.json` 单一源、生成 CSS、表达范式、无业务事实样例；生成器同时输出 TypeScript/Python token 映射。
- 已接入 Web 全局主题、共享导航、主要 cockpit/data/analysis/operations 样式、ECharts/SVG 财务图色板与离线驾驶舱预览。报表 Matplotlib 图表读取同一 token 映射；HTML/PDF、PPTX、XLSX 主要渲染器已接入主题映射，逐模板视觉与打印检查仍待完成。
- Web typecheck 通过；前端 37 个测试文件、201 项通过；调查表和全局原生表单控件视觉调整后，typecheck、全量 201 项前端测试及 Next.js production build 通过。视觉 token `--check` 和 `git diff --check` 通过。
- 2026-10-25：提交 `9cf65f6d58e0cdb33d8e04c17d843a8c9bbc1489` 下重采 20 路由×3 视口，60/60 内容就绪、API/浏览器错误/横向溢出/外部请求均为 0；60 张截图与 supplemental 引用已同步到覆盖报告。调查表按纸面风格修正，所有原生单选/复选控件改用古金品牌色。此轮截图矩阵关闭了默认视图加载和版面边界验收；最终视觉整改后仍需更新截图，逐图表、交互、无障碍和输出模板仍待验收。PR #5 的 dashboard 视觉回归暴露 Linux/macOS 两套截图基线都滞后于当前纸白/海军蓝主题与仪表盘版式。核对 CI 实际截图后确认这是已批准视觉更新，不是页面故障；更新 Linux 与 macOS 两组平台基线。隔离临时 Postgres/Redis/MinIO Compose 项目上，`scripts/test_dashboard.sh` 连续两次 7/7 通过，第二次为不更新快照的验收；同轮报告渲染器定向测试 21/21 通过。临时容器、专属数据库卷与 Compose 网络已清理。Linux 基线更新后的准确 SHA 全量 PR CI 尚待完成；此记录不代表视觉工作包完成。
- Playwright 截图覆盖 20 路由×3 视口；修复 `/operations` 报告查询 UUID 参数类型后，代码 SHA `9cf65f6d` 下最新矩阵重采，60/60 HTTP 200、内容就绪、API/浏览器错误、外部请求、横向溢出均为零；指标依赖图交互截图也在同一 SHA 重采。热力图渐变、财报分组柱与瀑布图已接入语义 token。20 张桌面图审阅后已调整共享链接/控件色、指标库古金强调线、模块落地页衬线标题/卡片节奏和财报页品牌强调色；红色财务负值语义保持不变。指标依赖图默认聚焦“常用”层，并保留“全部/专业”范围切换；图谱画布按当前节点层高度展开，默认截图 31 个节点可见、零错误；“全部”视图的高密度缩放仍待核。视觉差异与剩余顺序见[视觉覆盖验收](../../60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md#20-路由截图首轮差异盘点2026-10-24)：驾驶舱、财务出版页和数据工作台较接近；分析及功能范围较窄的页面仍有自然留白；逐图表、报告模板/打印、图表辅助表达、导入/映射与筛选交互、键盘焦点及对比度尚未验收。
- 2026-10-25：在 `9cf65f6d` 阶段基线上对 20 个默认桌面路由运行 Axe，发现 359 个色彩对比节点、7 个驾驶舱子页缺少 H1、1 个不可聚焦滚动区，以及调查详情的定义列表/landmark 语义问题。已在 `3e8a1676` 完成全站对比度与结构整改；准确结果为 Axe 4.13 桌面 20 路由零违规，且 20×3 矩阵为 60/60 ready。因此这项整改已关闭。后续顺序为：逐图表/数据表达核对 → 交互/键盘/200% 阅读 → HTML/PDF/PPTX/XLSX 版式与打印核验 → 最终矩阵和独立复核。
- 截图与逐路由结果在 [视觉覆盖验收](../../60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md)；synthetic manifest SHA 为 `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`，数据库只位于 `/tmp/flow-visual-audit-20261024`。
- 尚待完成的当前验收：逐页复核剩余概念板差异；逐图表核对期间、单位、图例、事实类型、来源与同值表达；验证依赖图全部/专业分层、导入/筛选/报告空错状态；完成完整键盘路径、实际 200% 阅读与窄屏交互；逐模板核验 HTML/PDF/PPTX/XLSX 版式与打印；完成最终独立复核及当前准确 SHA CI。当前 20×3 矩阵和 Axe 结果均已在准确代码 SHA `b04a7c5425c340681828f1c15c15f3071b1e2782` 下重采；之后如有视觉代码变更，应按结案时的最终代码 SHA 再重采。阶段矩阵只证明该 SHA 的默认态，不代表剩余图表、交互和输出格式已验收。

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
