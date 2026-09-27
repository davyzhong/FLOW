---
doc_id: FLOW-WI-UX-POST-DAMAI-001
title: 大麦数据后的剩余体验收口
doc_type: work-item
status: active
version: 5.15
created_at: 2026-09-24
updated_at: 2026-09-27
owner: FLOW
depends_on: [FLOW-WI-DAMAI-FULL-YEAR-001]
acceptance_refs: [FLOW-PLAN-INTEGRATED-EXECUTION-20260924, frontend-route-state-viewport-matrix]
applies_to: web-frontend
---

# 大麦数据后的剩余体验收口

> 2026-09-27 最新状态：`/reports`、`/data`、`/investigations`值级子项已关闭。最终代码 `3660389e` / CI `36310017180` attempt2 17/17 success；隔离verify19/19、GET矩阵159项零意外、Playwright12/12。当前唯一下一步为补齐Gate1全路由覆盖表、未覆盖下钻与全路由状态/视口矩阵，再执行Gate5；UX工作包仍 active。

## 指标库 `/metric-library` API→配置→UI 值级验收（2026-09-27；已关闭）

- 范围：逐项读取浏览器实际请求与页面 DOM，并与 `/api/v1/metric-library` 版本化字典及覆盖接口对账。通用/物流指标卡核验字段包括名称、公式/单位、时间行为、CAS/IFRS、口径/基准/勾稽、来源、执行类型、依赖、维度/分解、迁移、entry ID/修订入口和 MPM 信息；另逐条核验行业参考包、关系、CAS↔IFRS 映射、会计科目、准则、分录模板与治理事件。
- 公开与大麦覆盖接口分别和对应页面核对元数据/来源说明、汇总 KPI、快照标题及报告深链，并遍历 API 返回的每个快照×指标单元格核验页面显示值、缺失原因及 title。端点所用配置来自 `config/metrics/p5_metric_coverage_v1.yaml` 与 `config/metrics/damai_demo_metric_coverage_v1.yaml`；本轮是接口/页面展示一致性验收，不声称独立重算或裁定每项公开财务事实。
- 隔离大麦旅程：`bash scripts/test_damai_demo_e2e.sh`，verify19/19；只读矩阵159项（149预期200、10预期422、意外0）；Playwright9/9。Web Vitest143/143；生产构建导航/状态/响应式/深链 E2E93/93；`make typecheck`通过；`make lint`零错误、一条既有 TanStack Table warning。测试只使用专属隔离 Compose 卷，没有连接或写入常驻数据库；未修改指标源配置或产品实现。
- TDD 中两次红灯均来自测试断言未贴合真实页面合同：汇总 KPI foot 布局和 MPM 文案前缀；按已渲染 DOM 修正预期后，全套断言通过，没有删减覆盖或放宽断言。未发现本页 API/UI 值不一致。
- **交付状态：**本轮只扩充 `apps/web/e2e/damai-demo.spec.ts` 并同步状态文档；代码提交`71ea2dc9`同SHA CI run `36299600894` 17/17 success，M1/链接/plan views均通过，`/metric-library`页面子项关闭。唯一下一页为`/reports`（值级E2E编写与隔离复跑进行中）。UX Gate 1/Gate 5仍未关闭。

## 经营分析概览 `/operations` API→源事实→UI 值级验收（2026-09-27；已关闭）

- 范围：大麦FY2025/FY2026完整财报和公开经营披露的7个公司/期间，共9个上下文。页面E2E逐项比较安全 GET API 返回与浏览器请求、六主题状态、指标精确值及显示值、来源期间/页码/哈希、不可用原因、指标库口径链接、管理关注方向/内容和焦点链接。
- 发现并修复页面状态缺陷：用户切换报表/期间时旧 `overview` 会留在新上下文下，且请求失败时仍可能展示旧数。现在在上下文 change 事件立即清空 overview/freezeInfo 并切至 loading；组件测试覆盖延迟响应期间旧值消失、新值展示。组件回归7/7。
- 隔离验证：`bash scripts/test_damai_demo_e2e.sh` 使用独立 Compose project/卷；verify19/19；只读可见性矩阵159条（149预期200、10个不支持组合预期422、意外0）；Playwright9/9，其中本项遍历9上下文。Web Vitest143/143；经营 API pytest38/38；`make lint` 零错误（1条既有 TanStack Table warning）；`make typecheck`通过。常驻`flow`数据库未连接或写入。
- 验收脚本问题：首次复跑在初始上下文重复调用 `selectOption`，导致 `change` 清除 UI 但同值状态不会触发下一次 effect。按真实因果修正 E2E，不降低断言，之后全套隔离旅程9/9通过。
- **交付状态：**代码提交`0f8d92cf`；提交推送期间合并远端 README 自动截图提交`27babc32`，最终`main@8bd71798`。该确切SHA GitHub CI run `36293915314` 的17/17作业全绿；M1/链接/plan views均通过。`/operations`页面子项关闭；唯一下一页为`/metric-library`。整个 UX 工作包 Gate 1/Gate 5仍未关闭。

## 报告中心 `/reports` API→源事实→UI 值级验收（2026-09-27；已关闭）

- 范围：新增只读值级 E2E（不改产品实现），将报告中心四个列表与产物历史逐行逐格与安全 GET API 对账：客观财报分析报告列表对账 `/api/v1/statements`（公司/期间/报告类型/行项目数、objective-snapshot HTML 链接与查看分析深链）；经营报告快照列表对账 `/api/v1/operations/snapshots`（公司/期间/版本/指纹前缀、经营分析深链）；冻结候选下拉对账 `/api/v1/publishing/freeze-candidates`（期间/批次前缀/版本/已批准发现数，含 0 批准不可冻结禁用态）；报告快照列表对账 `/api/v1/publishing/snapshots`（版本/标题/日期），并核对其产物历史 append-only 表格与 attempts API 的行数/序号/格式/状态/大小/下载可用性逐格一致。该测试置于既有发布/上传两个变更旅程之前，全程只读。
- TDD 两次红灯均为测试自身缺陷，非产品缺陷：①Playwright `toBeDisabled` 辅助器对 `<option>` 误报 enabled（失败日志中 DOM 明确含 disabled 属性），改为直接断言属性合同；②`getByRole` name 默认子串匹配，「报告快照列表」同时命中「经营报告快照列表」，加 `exact: true` 修正。未发现本页 API/UI 值不一致。
- 隔离验证：`bash scripts/test_damai_demo_e2e.sh` 专属 Compose 栈，seed verify 19/19（ok=true、failed=[]）；Playwright 10/10（新增本测试后 9→10，第三次运行全绿）；`make typecheck` 通过；`make lint` 0 error（1 条既有 TanStack Table warning）。未连接/写入常驻 `flow`。
- **交付状态：**提交 `e869f259991830df2ac9e69929aa712f9677bf0c` 的 CI run `36306908435` 最终17/17 success；首次 `user-closure-e2e` 的 cleaning-summary GET 403 在同 SHA 重跑后通过，根因未知且未更改权限策略。报告中心页面子项关闭，唯一下一页为 `/data`。UX Gate 1/Gate 5仍未关闭。

## 数据工作台 `/data` 批次历史 API→UI 值级验收（2026-09-27；已关闭）

- 范围：只读对账数据工作台“最近的数据批次”表与当前 actor/企业可见的 `GET /api/v1/intake/batches`；逐行核验批次名称、状态、版本数、最新版本序号/状态、上海时区本地化创建时间和批次深链。测试放在会追加批次的上传旅程之前，不触发写操作。
- 测试来源：主线提交 `3660389e038083dfc92f6812c28e6ad7e2a2cfdb`；该提交同时带有后续 `/investigations` 测试，但本轮按串行计划仅关闭 `/data`，`/investigations` 仍为下一子项。
- 隔离验证环境：专属 Compose project `damai-demo-iso`、全新数据库/对象存储卷和大麦 synthetic release；seed verify19/19；只读可见矩阵159项（149预期200、10预期422、意外0；矩阵清单 SHA-256 `0416fe20234486cb1ca101cfbf6e650428b5df4750313c7cd5746eb8e8667786`）；完整 Playwright12/12；`make typecheck`通过；`make lint`零错误、1条既有 TanStack Table warning。验收后专属容器/卷已由脚本清理；常驻 `flow` 数据库未连接/写入。
- 同 SHA CI：GitHub run `36310017180` attempt2 17/17 success。attempt1 的 `smoke/make stack-up` 失败；同 SHA 重跑中 stack-up、API/Web health 与 worker ping 全通过，根因未取得，未改产品代码。
- **交付状态：**`/data` 页面子项关闭；唯一下一页为 `/investigations`。UX Gate1/Gate5仍未关闭。

## 调查归因 `/investigations` Finding 列表 API→UI 值级验收（2026-09-27；已关闭）

- 范围：主线提交 `3660389e038083dfc92f6812c28e6ad7e2a2cfdb` 中新增只读 E2E；对 `GET /api/v1/investigations` 的所有 Finding 逐行核对页面行数、类型、影响金额格式、比较口径、状态标签、评分及 `/analysis?run_id=` 链接；整行 `data-href` 根据 `finding_id`、`batch_id`、`metric_snapshot_id`、`analysis_run_id` 建立并与当前页面合同核对。按标题匹配行，不依赖 TanStack 表格排序。测试位于既有审核签发变更旅程之前。
- 值格式和状态标签与页面显示合同一致，未发现 API→UI错配。既有隔离旅程还会点击“进入调查”、定位收入增长 Finding 并完成审核签发；这些状态变更仅发生在隔离库。
- 环境/证据：`damai-demo-iso` 新鲜 Compose project/数据库/对象存储；`bash scripts/test_damai_demo_e2e.sh` seed verify19/19、只读矩阵159项（149预期200、10预期422、意外0）、Playwright12/12；`make typecheck`通过；`make lint`零错误/1条既有 warning。CI run `36310017180` attempt2 同 SHA `3660389e` 17/17 success，其中 `investigation-e2e` job success。attempt1 smoke `make stack-up`失败、attempt2通过；根因未知且未改产品实现。常驻 `flow` 数据库未连接或写入。
- **交付状态：**`/investigations`值级页面子项关闭。UX Gate1仍须补全所有路由/源事实证据、未覆盖真实下钻和全状态×视口矩阵；随后执行Gate5同 SHA全链验收，工作包不得提前关闭。

## 目标

让已装载的大麦合成数据在经分专员的核心页面中形成完整、可解释、可下钻的分析体验；明确区分“没有事实”“指标不适用”“快照未发布”“页面未展示”，不以空值补零，也不把静态 sidecar 说成已上线能力。

### 四问分析工作台值级审计（2026-09-27；局部页面交付，Gate 1 未关闭）

- `/analysis` E2E 不再只断言四个问题标题：真实隔离大麦 FY2026 报告逐项比对 API 身份、四问/十指标顺序、每项可用值、管理关注数量/方向/文案，以及财报和指标定义深链。
- 对工作台 API 的十个核心指标值，以同一财报详情端点披露的原始行独立复算并逐项对账：收入增长、净利润增长、毛利率、净利率、ROE、资产负债率、流动比率、DSO、盈利现金比率和自由现金流。大麦 FY2026 十项均可计算且与页面/API 一致。
- 根因发现：既有 DSO 把“期末应收 ÷ 年收入”直接当作天数。页面原显示 `0.3500`，按字典 360 天、平均应收余额和年度收入独立复算为 `116.3898` 天。现修正为 `360 × 平均应收 ÷ 年收入`；缺期初余额、收入非正时不出值。
- 核心十指标中的净利润增长、ROE、流动比率和自由现金流虽在主题合同及标准科目事实中定义，工作台计算器却未实现。现按指标字典补齐；盈利现金比率在净利润≤0 时拒绝输出失真倍数。平均余额缺期初值或分母不满足口径时保持 unavailable，不补零、不拿期末值冒充平均数。
- unavailable 状态传递主题合同中的具体不可用条件并在 UI 解释，不再将所有情况误标成“缺披露事实”；十个主题条件去除机器错误码，保留人可读语义。
- 验证：隔离 `make test-damai-demo-e2e` verify19/19、GET矩阵159项（149预期200、10预期422且零意外）、真实浏览器9/9；工作台 API 测试11/11、Web Vitest142/142、typecheck、目标 ESLint、ruff、mypy通过。财报详情不修改；常驻 `flow` 未触碰。
- 同 SHA 验收：提交 `bc8fa678` 的 GitHub CI run `36288403912`，17/17 作业全部 success。`/analysis` 值级子项已收口；后续唯一页面步骤为 `/operations`。本结果不代表工作包/Gate 1 已完成。

## 当前证据与判断（2026-09-26）

- 常驻开发库原 G2 于2026-09-25曾完成；2026-09-26按本工作包受控恢复步骤重新核验：先备份，再幂等 seed，之后 verify 19/19 两次均通过。备份为 `work/backups/flow-pre-demo-rehydrate-20260926.dump`（SHA-256 `b374a16ec72f3a918194b1b5b4c80a0df259fa4c56c920c1f1a6e9bd8ee9782d`，约228 KB）；收据位于忽略目录 `work/damai-demo/`，均不入 Git。
- 大麦 fixture 有24个月、1,920条经营实际、10,752条预算、4,800条应收回款、768条财务实际（含每月×4组织的 OCF）；40个客户、8个产品、6个区域、4个事业部。
- FY2025/FY2026发行财报静态工件现各51行项目；只读 API 与常驻数据库数据须按指定环境/SHA实测，不从静态工件推断常驻库当前结果。
- 大麦40项指标静态覆盖为 FY2025 37/40、FY2026 40/40；FY2025三项同比缺少FY2024比较期，不应补零或误标为企业不适用。
- 隔离验收中驾驶舱有8张KPI卡、12个月趋势、8个产品、4个客户群、2条发现；OCF KPI可用且趋势12/12完整。毛利矩阵32格中实际与预算比较各10格可用、空格保持 unavailable，整体仍为 `degraded`。
- 预测 sidecar 当前标记 `static-only` 且排除页面覆盖；本工作包不得把它计为已接入功能。
- Dashboard KPI 比较值若 API 状态为 `unavailable` 且原因码为 `*_not_published`，现显示“未发布”标签，并保留接口说明作为 title/accessible label；避免将破折号误解为零值。经营分析的比率/倍数/天数单位显示已按指标合同修正；其他页面的金额/数量格式仍需统一复核。
- 经营分析对真实大麦财报的复核发现：流动比率和资产负债率被误报 `not_applicable`，因为财报期末余额在归一化事实的 `end` 角色，而兜底只读 `cur`。现以同期间 `cur → end` 读取点余额；不得跨期回退。前端按指标合同格式化百分比、倍数和天数，保留原始精确值为悬停说明；未明确单位的经营事实保持原披露精度。
- 公式链复核再发现 DSO 已有 `ar_turnover` 可用，但依赖的指标 code 未被注入下游公式求值，因此误标 `fact_missing`。字典执行器现按声明顺序把已计算指标结果提供给依赖项；大麦 FY2026 DSO 按字典 360 天口径计算为 116.3881 天。
- 经营主题空态原先把所有 `not_applicable` 都标成“待内部数据”，会把“公开报告未披露分部数据”误导成“等内部授权”。现按原因码区分公开披露缺项、内部数据授权、期间分部披露缺失与缺少完整财报；未知原因仍保留原因码并显示通用不可用说明。
- Gate 1 扩展 GET-only 路由矩阵已在本机常驻 API 读取：40次请求、36个不同路由/参数组合，全部 HTTP 200。覆盖两份财报详情/投影/更正/四问/经营概览，7个公开经营期间，指标字典和两套覆盖矩阵，批次清单，2条Finding详情，客观快照、冻结候选及发布/经营快照和尝试列表。报告中心正式产物尝试为空列表（HTTP 200）；当前页面“尚未生成正式产物”与持久化状态一致，不应以常驻库模拟发布历史。
- 维度数据可见性修复已在 `649a2aba` 推送：完整产品/客群主数据仍供筛选使用；当前驾驶舱产品表与毛利矩阵仅展示当前发布快照确有事实的维度，并明确显示事实覆盖数/总目录数；完全无事实时呈现降级空态，不把空目录误报为完整或用零补齐。这是局部页面修复，不是全站 Gate 1 关闭证据。

### 视觉归档复验（2026-09-27，UX Gate 进度证据；非关闭）

- 共享 Next 开发进程的 `/statements` 请求挂起并出现 `EPIPE`，不属于本轮创建；未终止或改动该进程。改用 `work/damai-demo/web-matrix.E6MJjO/` 下的隔离前端副本及独立端口 54683 完成截图验收，复验后仅停止本轮创建的服务。
- 四个数据密集页面 `/statements`、`/reports`、`/metric-library`、`/investigations` 的五态（loaded/empty/loading/error/forbidden）×三视口（390/1024/1440）共 60 张图已刷新；归档生成器第61项写索引。Playwright 两轮均 61/61；第二轮额外断言每个状态下无未捕获页面异常。
- 首轮运行在旧指标库 fixture 中暴露 `MetricCard` 收到过时字段（`code` 而非 `metric_code`、缺 `domain` 等）导致浏览器运行时 TypeError。已将归档夹具修至当前 `flow.metric_dictionary.v1` UI 契约，并加入 pageerror 断言；归档复验无 pageerror。这个问题是测试夹具陈旧，并不表示生产 API 的指标数据缺陷。
- 代表性截图人审又发现报告中心 loaded fixture 未覆盖冻结候选、经营快照及对应尝试列表；首版因此把空占位错误地混入 loaded 图。已补齐这些端点的静态响应、将测试用的正式产物历史明确保持空列表，并重新生成归档；截图索引同步注明 loaded/empty 使用契约夹具，不能作为常驻库/大麦完整覆盖证明。
- 响应式 E2E 的 `frontend-responsive.spec.ts` 另有一份相同的旧指标字段 fixture；现已按当前 `MetricEntry` 契约修正，并对四个 fixture 数据页检查 `pageerror`。独立隔离 Next 副本 Playwright 27/27（11路由390px无横向溢出；四个数据页1024/1440及数据态通过，无未捕获页面异常）。
- 当前已推送基线 `33a99df1` 上重新执行真实大麦隔离旅程：迁移至 `0031_enterprise_directory`；发行 manifest SHA `6303595f01a3a4fb10bf90bf7320701107bb24aeedaad3e6ef9723bcd3e3bb3a`；seed 后 verify 19/19；隔离安全 GET 矩阵 43/43 全部 200，矩阵 manifest SHA `7065dfcbd7c7f12029bf901266cc1342cbd2d50a448b0ce34c8f22295b5e7231`；真实浏览器旅程 9/9，含报告产物下载 SHA 对账与数据工作台上传旅程。脚本完成后 `damai-demo-iso` Compose 服务无残留；本次不触碰常驻 `flow` 数据库。

### Dashboard API→UI 逐项对账加固（2026-09-27，UX Gate 进度证据；非关闭）

- 在真实大麦 Playwright 旅程中增加 API→页面值级断言：8张 KPI 卡的数量、唯一标题、主值，以及预算/同比/YTD预算三类比较的状态和值，必须逐项等于 `/api/v1/dashboard/overview` 响应。
- 展开 Dashboard 趋势明细，将同响应的12个月、每月收入/经营利润/经营现金流/毛利率共48个显示值和月份逐项核对；OCF 仍额外要求12/12可用且 exact value 非空。
- 将毛利矩阵与同响应做32格完整对账：行列名称/数量正确；每格 actual/comparison 显示值与 API 一致；无事实的格必须显示破折号而非0。
- 产品经营表现表也逐产品核对名称、收入、收入同比、订单量、订单同比、毛利率、毛利率同比和履约成本率七项显示值，与同一 API 响应一致。
- 只读探测矩阵现对四类维度的每个选项分别请求 `month` 与 `ytd` 视图，不再仅取每类首个选项；矩阵 builder 单测3/3通过。隔离旅程已扩展至85条 GET，85/85 HTTP200；可见性清单 manifest SHA `fad8696a8f00d5d53f0ac1ac4c5e371378f266e7502648b1c5d813b57a69d35e`。清单含运行期快照/ID，manifest SHA 每轮变化，仅证明本次完整性，不是稳定发行包 SHA。
- 本轮 `make test-damai-demo-e2e` 在隔离 Compose 项目中验证迁移头 `0031_enterprise_directory`、seed发行 manifest SHA `6303595f01a3a4fb10bf90bf7320701107bb24aeedaad3e6ef9723bcd3e3bb3a`、verify 19/19、只读 GET 85/85 HTTP200、真实浏览器 9/9；隔离 Compose 卷与服务由脚本清理，未触碰常驻 `flow` 数据库。
- 验证：Web Vitest 142/142；矩阵 builder pytest3/3；本次修改后的 `pnpm exec tsc --noEmit`、目标 E2E ESLint 通过；前一检查点截图归档61/61与响应式E2E27/27通过。当前筛选 API 探测覆盖全部单维选项×两个期间，但尚未穷举多维交叉组合，UI筛选器也仅有代表性 E2E；此代码仍须提交后的同 SHA required CI。
- 尚未关闭：其它数据页面的逐项 API→源事实→UI 映射、所有显示数据的深链逐点检查、其余交互路由的全状态/全视口矩阵及 Gate 5 干净 SHA 全链。Dashboard筛选合同与交互已完成本地/隔离验收，Dashboard与财报详情的值级核验已有交付；均不代表 UX Gate 或工作包可标 completed。

### 筛选能力矩阵与 UI 交互复验（2026-09-27，当前状态覆盖前文旧筛选状态；非关闭）

- Dashboard 筛选合同以 API `filter_options.supported_combinations` 为准：支持全局、任一单维、客户群×物流产品；其它维度对返回 422 `unsupported_filter_combination`。
- 只读矩阵覆盖 159 项：149 项预期 HTTP200（基础路由、四类维度全部值×month/ytd、客户群×物流产品全值组合×month/ytd），另有10项代表性不支持组合（五种不支持维度对×两种期间）按指定错误码拒绝；意外状态/错误码为0。清单 SHA `4f9e45c1c668d725cc28f6eb17dd0add223bb48e0205e15fee52f7534866ba63`，含运行期快照ID，只作本轮证据。矩阵 builder pytest3/3。
- 浏览器实际操作 YTD 与组织/客户群/产品/区域四个 selector，逐项断言控件值、URL query、对应 API `active_filters` 和8张 KPI 卡显示值/比较状态一致。隔离旅程：seed发行 manifest SHA `6303595f01a3a4fb10bf90bf7320701107bb24aeedaad3e6ef9723bcd3e3bb3a`、verify19/19、矩阵159项（149 expected200 + 10 expected422，零意外）、浏览器9/9；隔离栈清理完毕。
- 首次将所有维度对的笛卡尔积都强制期望200，暴露324个合同性422并产生隔离PostgreSQL约6GB读取流量；根据 API 支持合同修正为“合法客户群×产品全值组合 + 其它维度对代表性错误码验证”。本次全矩阵约1.2分钟通过；此全量 pairwise 用于 UX Gate，不应无必要放进常规快速 smoke。
- 验证：`make lint && make typecheck && make test-web`（Web142/142；lint零错误、一条既有TanStack Table warning）、矩阵pytest3/3、plan views、文档M1、链接、contracts均通过；E2E目标 ESLint/typecheck通过。此代码须提交后的同 SHA required CI。
- 延伸值级验收（`main@99991566`）：隔离矩阵现为159条（149条合同有效请求预期200、10条不支持组合预期422且错误码正确、意外0）；完整覆盖单维选项×month/ytd、客户群×产品支持组合及五种不支持维度对。脚本 pytest3/3；seed verify19/19；浏览器9/9；Web142/142；lint/typecheck通过。后续不得把不受支持组合记为缺陷。
- 同 SHA CI：run `36279509026`（head `9999156690fdb42edc76488f271ae877abe73406`）及文档跟进 run `36279766191` 均已 success；最新 `104da533` 与 `78722e73` CI 待终态。
- 隔离复验（2026-09-27）：使用本轮专属 Compose 项目 `flow-ci-repro`（PostgreSQL 55432、Redis 16380、MinIO 19010；独立卷），空库迁移至 `0031_enterprise_directory`；目标单测首次通过、模块3/3通过；CI同范围集成批次命令 `pytest tests/integration tests/investigation tests/copilot tests/api -q --ignore=tests/api/test_auth_boundary.py --ignore=tests/api/test_workspace.py` 结果 **267 passed, 3 warnings**；批次结束后目标单测再次通过。旧失败截至此证据仍不可复现，根因未知；不改实现、不降低断言，须结合当前 SHA CI 终态继续观察。
- 财报详情值级验收（`main@78722e73`）：依据真实隔离 `/api/v1/statements` 列表选 FY2026 并读取详情 API；逐 section、逐原文行、逐非空余额/发生额/上期列核对页面行数、顺序与显示。页面值按 `unit_note` 缩放，tooltip 保留的原始精确值逐项比对；FY2026 `stock_code=DAMAI.SYN`、来源路径在 `fixtures/damai/statements/`。`make test-damai-demo-e2e`：verify19/19、GET矩阵159项（149×200、10×422合同拒绝、0意外）、浏览器9/9；`pnpm exec tsc --noEmit` 与目标 ESLint 通过。测试先后暴露并修正两处测试假设错误（stock_code/source_ref混淆、包含文本命中同名行），依真实 API schema 和行序更正后全绿；未发现生产数据映射缺陷。该提交同 SHA CI `36282388214` 尚待终态。
- 历史 CI 异常：旧 SHA `cc2211e5` run `36276782059` 曾有 `tests/integration/test_metric_impact.py::test_impact_report_traverses_downstream_and_sandbox` 单例失败（88项中1失败，`SandboxDiff.current_value=None`，原测试预期非空）。本轮隔离复验目标单测两次、模块3/3、CI范围集成批次267项及批后单测均通过；截至 `99991566`、`d836a6ca` required CI success，尚无复现，根因仍未知，保留历史观察，不称为代码修复。
- 本工作包仍 active：其它页面 API→源事实→UI 映射、深链逐点检查、其余交互路由全状态/全视口矩阵与 Gate5全链尚未关闭。

### 真实大麦 API→页面交叉对账（2026-09-27，Gate 1 部分闭环）

本表只记录在 `33a99df1` 同源代码上完成的隔离旅程和已有已提交验证；页面五态截图夹具不被当作业务数据证据。

| 路由/页面 | API / 发行事实 | 浏览器可见证明 | 当前缺项的正确归因 |
|---|---|---|---|
| `/` 驾驶舱 | `/api/v1/dashboard/overview` 及组织/客群/产品/区域四类筛选；8张 KPI、12月趋势、32格矩阵 | 真实 E2E 校验四粒度筛选均来自大麦维度；OCF KPI 与12/12趋势有值；毛利矩阵有10格实际、10格预算比较 | 其余22格没有实际源组合，保持 `null` 并将矩阵标为 degraded；不得补零。客群粒度部分利润/OCF不适用，是指标粒度限制，不是请求失败 |
| `/statements` 财报分析 | `/api/v1/statements` + FY2025/FY2026详情；大麦合成企业年度报告各一份 | `78722e73`隔离E2E逐报告、section、原文行及所有非空披露值核对API→页面缩放值与原值tooltip；9/9旅程通过 | 当前无月度公司财报，产品合同按年度报告验证；不应把物流月度事实伪装成月度法定财报。此页值映射通过，深链及跨视口状态仍列于整体Gate |
| `/analysis` 四问工作台 | `/api/v1/analysis/workbench/{report_id}`；两个财报期间各有可分析上下文 | 浏览器选中 FY2026，展示四个分析问题；此前 FY2025 `metric_code` 响应模型500已修复且列入只读矩阵 | 已确认的契约错误已修复；Gate 5 仍需干净 SHA 回归。四问输出是系统生成判断，发布仍需经分专员审核 |
| `/operations` 经营分析 | 两份内部年报概览、7个公开披露期间，共9个分析上下文；六主题面板 | E2E 选取 FY2026完整财报，确认六主题可见；既有 API 对账显示七项运营效率指标可计算 | 来源未披露的分部值/内部数据缺项按原因码显示 unavailable，不推定为零或“等授权” |
| `/metric-library` 指标库 | 指标字典65项；大麦年度覆盖矩阵40项 | E2E 明确看到 synthetic 大麦矩阵、FY2025 37/40 与 FY2026 40/40 | FY2025 少3项是缺少FY2024比较期，不等于大麦公司不适用；指标定义存在不等于底层事实齐全 |
| `/reports` 报告中心 | 发布快照、冻结候选、经营快照及 attempts 安全 GET | E2E 在隔离栈选择大麦经营快照、生成产物并按下载 SHA 对账；UI 合同截图中的无产物状态仅是 mock，不代替此旅程 | 某一运行若 attempts 为空，表示该环境没有已生成产物，不是下载按钮故障；禁止在验证时对常驻库触发发布/冻结 |
| `/data` 数据工作台 | `GET /api/v1/intake/batches` 只读列当前 actor/企业可见历史；隔离旅程上传工作簿 | 历史可见性有 API/E2E 覆盖；完整上传→映射→校验→发布旅程在隔离库通过 | 页面历史受当前 actor/企业权限过滤；不得因其他 actor 的批次不可见就判作批次不存在 |
| `/investigations` 调查归因 | Findings 列表及详情 GET，种子有两条分析发现 | E2E 打开收入增长 Finding，批准签发后可见已签发状态（只发生于隔离栈） | Finding 必须追溯批次、快照与证据；无已登记 finding 关联不得虚构深链 |
| `/public`、`/internal` 模块入口 | 静态模块导航落地页 | 导航链路属于页面一致性测试 | 页面本身无报表是设计排除；公开数据入口实际在 `/operations` 分析上下文中，不计成缺失数据页 |
| `/login` | 认证入口 | 现有路由清单单独测试 | 登录页是 shell/数据态规范的显式例外，不参与经营数据覆盖统计 |

**本表结论：** 可复验的大麦页面旅程覆盖已建立。Dashboard值及筛选合同/交互、财报详情所有已显示披露值已逐项对账；Gate 1 仍缺其它页面逐值交叉核对、所有目标页可见下钻的逐点验收、其余路由状态/视口完整矩阵，以及 Gate 5 同 SHA 全链。不得把 159 条 API 请求全数符合合同或 9 条旅程 E2E 单独等同于全站 UX 通过。
- 当前矩阵仍有明确范围差距：归档截图只覆盖四个数据密集页；其余七个交互路由仅有既有移动端溢出测试/局部状态合同，尚无五态×三视口全量视觉证据。截图中的单个财报/单指标 mock 是稳定的展示夹具，不是大麦数据库实况，也不能据此断言实际大麦数据的页面完整性。
- 此复验只补充视觉归档与测试真实性，不覆盖 Gate 1 的逐项 API→发布对象→源事实映射，也未覆盖所有目标指标/趋势/矩阵下钻；工作包仍保持 active。

## 实施路线（本文件是规格；实施须按用户已批准的工作状态执行）

### Gate 1：逐页数据链路和缺口归因

盘点驾驶舱、报表分析、指标库、应收/经营分析、报告中心、数据工作台和公开经营分析页，建立“页面 → API → 已发布对象 → 源事实/指标”的覆盖表。每个空白/缺值只能归入：源事实不存在、口径/映射缺失、计算失败、快照未发布、过滤条件不匹配、前端未消费、按设计排除之一，并附可复现证据。

Files:
- Inspect: `apps/web/components/dashboard/`, `apps/web/components/statements/`, `apps/web/components/metric-library/`, `apps/web/components/operations/`, `apps/web/components/reports/`, `apps/web/components/data/`
- Inspect: `services/api/src/flow_api/dashboard/`, relevant statement/metric/operations API routes
- Evidence: add a versioned coverage table to this work item or its linked verification record; do not create another status ledger.

Acceptance: Gate 1 覆盖表必须逐项记录精确路由、请求参数/筛选、公司/组织、期间、数据集/批次、环境标识和 Git SHA；同一环境与 SHA 下冻结脱敏后的 GET 响应摘要或内容哈希。每个目标页有真实 GET 响应证据；缺口均有分类与 owner；已发布但未展示、或页面声称完整但 API 缺值的情况不得留作“无数据”笼统结论。

只读验收的安全边界：不得仅凭 HTTP 方法判定路由无副作用。代码审查已发现以下 GET 会调用 freeze 并可能新增客观快照：`GET /api/v1/statements/{report_id}/objective-snapshot`、`GET /api/v1/statements/{report_id}/objective-snapshot/html`、`GET /api/v1/operations/overview/{report_id}/{html|xlsx|pptx|pdf}`。这些端点必须从 GET-only 探测矩阵排除；保留为单独的 API 语义/发布行为评审项。在明确完成只读保证或获得显式状态变更授权前，不得用浏览器、curl、探测器或 CI 对它们做“只读”请求。

### Gate 1 诊断盘点（2026-09-26，只读；代码验收仍未关闭）

API 由本 worktree 的 `uvicorn --reload` 提供服务。最新整轮只读探测前后，运行时代码 overlay 指纹保持一致：Git 基线 `3ff95115` + 工作树 overlay SHA-256 `1ede264890932aefc595540885a3cc34feb891f7516a137637db8bab3723529d`。响应哈希与复现参数见[Gate 1 API 证据记录](../../60_delivery/verification/2026-09-26--damai-visibility-gate1-v1.md)。这是可复现的诊断快照，不是干净提交 SHA 的发布验收；源文件仍包含其他会话的未提交改动，不能据此宣称代码版本已验收。

| 页面 | 读取链路（观察到的 GET） | 初步观测 | 归因 / 待办 |
|---|---|---|---|
| `/` 经营总览 | `/api/v1/dashboard/overview?period_view=month\|ytd`（全公司、无维度筛选；截至2026-08） | 8 KPI卡；12个月趋势点、每点4指标；8产品、4客群、32格毛利矩阵。经营现金流趋势12/12不可用，码 `trend_metric_not_published`；经营现金流KPI主值1/8不可用、码 `metric_grain_not_published`；预算4/8及YTD预算4/8不可用、码 `comparison_not_published`；矩阵实际22/32为 `metric_grain_not_published`、比较24/32为 `comparison_not_published`；整体 `degraded`。顶层质量、对账、快照/分析发布与新鲜度状态均显示通过/已发布/新鲜。 | 主要是快照/指标粒度和比较值未发布，不是可以用补零处理的数值缺失；需追到快照构建、发布和聚合层。 |
| `/statements` 财报分析 | `/api/v1/statements` → `/api/v1/statements/{report_id}` | FY2025、FY2026各1份；每份40行：资产负债表15、利润表13、现金流量表8、权益变动表4。 | 年报期间已存在；月度财务报表是否属于范围须按产品合同裁决，不擅自扩成另一个口径。 |
| `/analysis` 四问工作台 | `/api/v1/statements` → `/api/v1/analysis/workbench/{report_id}` | FY2025 初始返回500；确定性提示 `leverage_rising` 带 `metric_code`，原响应模型却 `extra=forbid` 且未声明该字段。补齐响应契约后，本地热重载 API 返回200并带指标代码。FY2026原为200。 | 根因已确认并修复（`ManagementWatchItem.metric_code` 缺失）；回归测试已覆盖。待变更提交后在干净 SHA 复测；其余页面缺口仍需逐项归因。 |
| `/operations` 经营分析 | `/api/v1/operations/public-periods`、`/api/v1/operations/public/{stock_code}/{period}`、`/api/v1/operations/overview/{report_id}` | 公开期间清单7项（菜鸟5、大麦2）+两份大麦完整财报，共9个可选分析上下文；全部上下文均读取200，六主题结构可见。大麦FY2026七项运营效率指标现全部可算。 | 主题原因码现分别说明披露缺项/内部授权/期间缺失；周转格式已修复。完整视口/403/加载/错误态与全站所有下钻仍待验。 |
| `/metric-library` 指标库 | `/api/v1/metric-library`、`/api/v1/metric-library/coverage?dataset=damai` | 65个定义、40项覆盖矩阵；FY2025可计算22项、FY2026可计算25项。未满足项的接口缺失字段为：利息费用 `is.interest_exp(cur)`（7项指标）、短债 `bs.short_debt(end)`（3项）、长债 `bs.long_debt(end)`（1项）、应付账款 `bs.ap(end)`（2项）、同比基期 `is.revenue/net_profit/operating_profit(prev_yoy)`（3项）、销售收现 `cf.cash_from_sales(cur)`（1项）、资本开支 `cf.capex(cur)`（1项）。 | 接口的 `missing` 只证明归一化事实缺失，不足以判断原件未披露、导入映射漏项或该指标对大麦不适用；Gate 2须逐项回看原始合成报表及公式合同后分类，不能将财务费用直接冒充利息费用。 |
| `/reports` 发布中心 | `/api/v1/publishing/snapshots`、`/api/v1/publishing/freeze-candidates`、`/api/v1/operations/snapshots` | 1个发布快照、12个冻结候选、2个经营快照。 | 核对候选/发布状态、期间与数据集。 |
| `/data` 数据工作台 | 当前界面为会话内上传/映射/校验；没有页面初始态批次 GET | 已 seed 的批次在此页不可通过历史列表浏览；仅有已知 batch ID 后查询版本的 API 路径，没有通用批次列表入口。 | “数据在库但无浏览入口”，纳入 Gate 4，不应误判为源数据不存在。 |
| `/investigations` 与详情 | `/api/v1/investigations`、`/api/v1/investigations/{finding_id}` | Finding 列表2条。 | 核对每条发现的事实、证据与财报关联。 |
| `/public`、`/internal` | 模块导航落地页 | 页面本身不展示业务数据。 | 不计作数据页；其链接目标页纳入本表；登录页排除。 |

**Gate 1 诊断盘点已完成；实现/发布验收仍未关闭**：只读 API 矩阵、请求口径和初始响应哈希已冻结。FY2025 工作台 500 根因已确认并在本地工作树修复：确定性 `leverage_rising` 提示携带 `metric_code`，严格响应模型漏字段导致校验失败；新增回归测试由红转绿，本地 API 重测返回200。其余缺口仍须逐项归类并指定后续 Gate；当前工作树含其他会话改动，待拥有者整理提交后，再以干净 SHA 重跑完整矩阵作为代码验收基线。不得覆盖、暂存或提交其他会话的变更。

#### 补充缺口码读数（2026-09-26，只读，未冻结响应哈希）

本轮继续从当前热重载服务 GET 读取到精确缺口码：驾驶舱12个月现金流趋势全部为 `trend_metric_not_published`；8张卡中现金流KPI主值为 `metric_grain_not_published`，4张预算及4张YTD预算比较为 `comparison_not_published`；毛利矩阵32格中22格实际值为 `metric_grain_not_published`，24格比较值为 `comparison_not_published`。该证据把责任收敛到 Gate 3 的指标快照粒度/趋势发布/比较快照生成，不可误归为“数据库无业务数据”。指标库覆盖接口列出的18个缺失规范事实字段，已分组记录在上表；是否属于源事实缺失、导入映射或不适用仍由 Gate 2裁定。此补充读数未绑定新的工作树内容哈希，须在稳定提交版本重新冻结。

### Gate 2 静态事实生成结果（2026-09-26，待本轮提交）

- 每份生成财报现为51行：利润表14、资产负债表20、现金流量表13、权益变动表4；新增项有明确的 synthetic 说明且不改变既有总额。
- 导入/归一化测试覆盖7项新事实映射：利息费用、应付账款、短/长期借款、销售收现、资本开支、折旧与摊销。
- 覆盖工件与本机只读 API 均为 FY2025 37/40、FY2026 40/40；FY2025 剩余 `revenue_growth`、`net_profit_growth`、`operating_profit_growth` 无FY2024比较列，按该期间不适用，不补零。
- 财报/映射/归一化相关测试24项通过；ruff、mypy、财报发行包 `--check` 通过。覆盖工件重复生成 SHA-256 保持 `e256bc20ccf1283465ffe6e4d997de6209a335ad4ba874208ff8d85d8678f0fb`。
- 以上是静态发行与 `flow_test` 测试证据；常驻 `flow` 未写入。新行尚未通过隔离发布旅程装入页面数据库，不能宣称用户当前开发库已显示51行。

### Gate 2：形成正确且够用的合成财务事实

先把40个指标按“适用且可计算 / 适用但源事实缺失 / 不适用 / 有意不展示”裁决。原装载数据 FY2025/FY2026 初始覆盖为22/40、25/40；修订生成器补齐7项确定性合成事实：利息费用、短债、长债、应付账款、销售收现、资本开支、折旧与摊销。逐项复算后覆盖为 FY2025 37/40、FY2026 40/40；剩余三项仅为 FY2025 同比增长指标，因24个月数据包无FY2024而列为“该期间不适用”，FY2026 使用FY2025比较列均可计算。新增事实从既有年度经营/资产参数推导，不改变收入、成本、OCF/ICF及现金桥总额；遵守报表勾稽、单位/币种和24个月合同，不以零代缺值。

合成财报的计划事实表达：利息费用作为财务费用的明确子项披露，不重复计入利润表费用小计；短期借款、应付账款拆入流动负债合计；长期借款拆入非流动负债合计；销售收现、资本开支写入现金流明细且保持现金流入/流出小计、OCF/ICF、现金桥原值闭合；折旧与摊销由固定资产基础推导并作为现金流补充披露、不改变净现金流。数额必须由现有确定性参数/年度事实推导并明确 synthetic 假设，不能覆盖既有总额。

Files:
- Modify as evidence requires: `services/api/src/flow_api/fixtures/damai/statements.py`, `config/statements/item_alias_map_v1.yaml`, `scripts/build_damai_metric_coverage.py`, `scripts/build_damai_demo.py`
- Regenerate only through generator: `fixtures/damai/canonical/`, `fixtures/damai/statements/`, `fixtures/damai/manifest.json`
- Tests: existing `scripts/tests/` and API fixture/metric tests; add focused regression tests for every newly computable metric and accounting invariant.

Acceptance: 40项指标逐项有“适用且可计算 / 适用但缺源事实 / 不适用 / 有意不展示”结论；当前裁决为 FY2025 37项可算+3项同比不适用、FY2026 40项可算。新增7项事实的映射来源唯一、别名无歧义；逐项将覆盖矩阵数值和缺失原因与 API 响应对账；BS、IS、CF核心恒等式、子项到小计勾稽和预算/实际勾稽通过；重复构建零漂移。静态发行文件完成不代表常驻库已重载；导入须在隔离验收栈验证。

### Gate 3：修快照发布与分析聚合

追踪当前驾驶舱降级到具体月度快照、源事实和指标定义，修复快照生成/发布或聚合逻辑中的已证实根因；验证 24 个月趋势、预算对比、同比/环比以及客户群、产品、组织、区域筛选。月度 API 只展示当前已发布且口径一致的快照；未满足条件的值保留显式缺失原因。

#### Gate 3 根因补充（2026-09-26）

常驻数据库只读核验发现：`damai-demo-v1` 已导入的 `fact_financial_actual` 每月每组织只有 7 个科目（REVENUE、三类直接成本、GROSS_PROFIT、OPERATING_EXPENSE、OPERATING_PROFIT），没有 `OPERATING_CASH_FLOW` 实际；预算事实中有 OCF。虽然 `ManagementAccount` 已定义 OCF，且 `build_damai_package()` 已生成带 E5 利润-现金背离的月度 `cash_flow[].ocf`，但 `fixtures/damai/canonical.py::_financial_actuals()` 没有消费这组现金流值，因此 canonical `financial_actuals.jsonl` 与已导入实际均漏掉 OCF。现有指标快照逻辑按源科目精确匹配，故 OCF actual 缺席是上游事实未传递，不是快照发布器漏算。禁止直接修改计算器或给缺值补零。

首个根因修复已在 canonical 生成链路完成并推送（`4932504`）：从既有 synthetic `cash_flow[].ocf` 推导并写入 24 个月×4 组织的 OCF actual，按同月组织收入占比分摊并保证公司总额守恒（尾差归末组织）；canonical 合同测试、指标粒度对账测试与发行 manifest 已更新。全量 canonical 测试25项、OCF/财务快照粒度对账3项、发行包确定性 `--check` 均通过。隔离 Compose seed、对象存储校验与 verify 19/19通过；浏览器 E2E 9/9 未通过，原因是验收 Next 实例和已有开发服务器共用 `apps/web/.next`，第二实例报“Another next dev server is already running”，随后页面连接被拒。禁止终止未知/已有开发服务器；重跑前应由验收脚本给 Next 配置本次运行独有的 `distDir`，清理时只删除该专属目录。隔离导入后的 API/UI OCF 趋势仍待复验；常驻 `flow` 库只读，不得重灌。毛利矩阵 grain/comparison 缺失仍需独立追查。

**后续复验更正（2026-09-26）**：给 Next 指定独立 `distDir` 后，浏览器 8/9 通过，唯一失败是旧 E2E 仍断言 OCF KPI `unavailable`，实际 API 返回 `available`。这证明快照链路已能提供 OCF KPI；页面/API 中其余8项均通过。Next 会将自定义目录写入工作区的 `tsconfig.json` 与 `next-env.d.ts`，因此专属目录虽能避开锁，但不能直接在真实工作目录使用。下一轮先更新断言为 `available` 且值非空，再将 web 源复制至 `work/damai-demo/` 下的唯一临时目录、复用 node_modules 链接后运行 Next，避免改写工作区配置；脚本只清理本次创建的副本。

**最终隔离页面验收（2026-09-26）**：验收脚本改为临时 web 工作副本后，`bash scripts/test_damai_demo_e2e.sh` 全程通过：verify 19/19、八页面/旅程 E2E 9/9。Dashboard API 的 OCF KPI 为 `available` 且值非空；12个月趋势 `complete`、覆盖12/12，所有月度 OCF 值均 `available` 且非空。临时副本和隔离 Compose 卷已自动清理，常驻库未写入，真实工作区 TS 配置未被验收脚本改动。本轮关闭“现金流源事实遗漏/快照缺失”这一类缺口；毛利矩阵实际与比较值缺项仍需独立定位，当前整体 Gate 1 与工作包不得因此关闭。

#### 毛利矩阵缺格根因（2026-09-26，只读核查；实现待验收）

静态 canonical 经营实际在全量期间只含10种客群×产品组合；2026-08 的实际毛利快照也只有10个组合，而同比毛利只有8个组合。缺少的组合在源实际中没有对应经营事实，不能以零补齐或伪造毛利。数据库中的预算毛利覆盖32格，但预算差异只覆盖10格。最新本机只读 API 返回32格、实际可用10格、同比可用8格，并把比较标签整体标为“不可用”。这次 API 读数来自热运行栈，未绑定干净提交 SHA，作为归因线索而非发布验收证据。

服务逻辑曾要求某种比较值覆盖全部32格，才选择预算/同比；两者均不满足时退回同比，因此丢弃了覆盖更高的预算比较。修复后按同一矩阵实际可比格数选择单一比较口径，优先覆盖数更多者、同数时预算优先；没有已发布值的格保持显式 unavailable，矩阵整体仍 degraded，不做零填充。格级 `metric_grain_not_published` / `comparison_not_published` 继续表达“快照无该值”，不擅自改标为“无业务活动”或“不适用”。

修复验收（2026-09-26）：`bash scripts/test_damai_demo_e2e.sh` 隔离旅程通过，verify 19/19、E2E 9/9；新增驾驶舱 API 断言实测32格、实际10格、预算比较10格、比较标签“预算”，并确认无实际值的格 `exact_value=null`。Dashboard 测试13项、前端 typecheck、ruff、mypy均通过。该轮运行来自含其他会话未提交文件的共享工作树，但改动文件已明确隔离；因此它是功能验收证据，不替代提交后的 CI 与干净 SHA Gate 1复测。常驻库保持只读。

CI 纠偏（2026-09-26）：`5510bad3` 的 GitHub Actions integration 因历史测试断言失败（将 FY2025、FY2026 都要求 `computable < total`）而失败；静态发行矩阵与 Gate 2 合同明确为 FY2025 37/40、FY2026 40/40。将断言改为精确校验这两个期间覆盖数，未放宽缺口真实性检查（仍要求至少一个缺失格且每格 display/missing 互斥）。本地同文件另有未提交的映射测试，按 CI 工作目录（`services/api`）运行后，该修正用例通过 1/1；仅暂存独立断言 hunk，保留其余并行改动不提交。修正提交后的 CI 尚待结果。

Files:
- Inspect/modify if root-caused: `services/api/src/flow_api/fixtures/damai/canonical.py`, `services/api/src/flow_api/fixtures/damai/generator.py`, `services/api/src/flow_api/dashboard/fixture.py`, `services/api/src/flow_api/dashboard/repositories.py`, `services/api/src/flow_api/dashboard/service.py`, `scripts/seed_damai_demo.py`, `scripts/test_damai_demo_e2e.sh`, `apps/web/e2e/damai-demo.spec.ts` and the owning metric snapshot service
- Tests: `services/api/tests/fixtures/test_damai_canonical.py`, `services/api/tests/fixtures/test_damai_metric_grain.py`, `services/api/tests/dashboard/` and dashboard API integration tests

Acceptance: 形成逐条 `degraded` reason 对照表，明确每条当前原因须消除还是合理保留及其证据；对 Gate 2 的40项指标逐项把“覆盖矩阵→API 返回值/缺失→驾驶舱或报表展示”对账。所有声明应完整的面板无非预期 `degraded`；24个月时间序列可核对；过滤前后总额、预算差异和明细 drill-through 可复算。若降级是有意且合理，必须明确展示面板级原因，而非静默缺项。

### Gate 4：页面可见性、可理解性和下钻

让页面直接显示当前选择期间、数据批次/新鲜度、口径、可计算覆盖与明确缺口；建立从 KPI/趋势/矩阵到筛选明细或财报原行的真实链接。覆盖 390/1024/1440 视口、加载/空/错误/403/部分降级状态。和全站深链实施计划协同，不重复实现已完成的批次一。

Gate 1 已证实 `/data` 初始状态没有历史批次 GET，已发布批次不在页面可发现。补齐只读 `GET /api/v1/intake/batches` 与页面历史列表：仅返回当前企业中由当前 Principal 创建的 `internal` 批次；新批次写入当前 actor 的 `created_by`；历史默认最多50条、按创建时间倒序，并提供版本数/最新版本状态。不得列出他人或跨企业批次；旧 `legacy/public` 无可靠所有权的批次不列入此端点。无 schema 迁移，复用既有 `INTAKE_VERSION_READ` action 和 enterprise scope policy。

#### Gate 4 批次历史子项（2026-09-26，本地验收完成，CI待验）

- 新批次由已授权的 Principal 写入 `created_by`；现有旧默认值保留给低层 fixture/历史兼容，不作为新 API 创建者来源。
- `GET /api/v1/intake/batches` 复用 `INTAKE_VERSION_READ` 与 `load_single_enterprise`；查询同时约束 `module_kind=internal`、Principal actor 和企业 ID，按创建时间倒序，最多50条，版本数与最新版本状态由只读子查询投影。
- `/data` 初始页展示批次名称、批次状态、版本数、最新版本状态、创建时间；支持 `?batch=` 历史批次识别及越权/不可见提示。此视图是历史索引，不承诺恢复编辑会话或修改已发布版本。
- 验收：`tests/api/test_intake.py` + `tests/security/test_route_policy.py` 18 passed；`apps/web` `data-workbench.test.tsx` 16 passed、typecheck/eslint 通过；API ruff/mypy 通过；`scripts/check_contracts.sh` 与 `python3 scripts/check_docs.py --phase m1` 通过。`scripts/test_damai_demo_e2e.sh` 隔离复跑 seed/verify 19/19、浏览器 E2E 9/9。常驻 `flow` 未写入；API 测试使用隔离 `flow_test`。
- 新增路由后授权清单与 OpenAPI/TS 契约已同步；提交 `430020f` 已推送。提交 `430020f` 与文档提交 `59b328dc` 的 GitHub Actions 均出现 dashboard job 环境变量冲突（见 Gate 5 回归记录）；批次历史代码本身本地和干净 SHA Damai E2E 已通过，但 Gate5 CI仍未通过。
- 干净 SHA 复验：临时 detached worktree `59b328dc` 上独立安装依赖并运行 `scripts/test_damai_demo_e2e.sh`，seed/verify 19/19、浏览器 E2E 9/9通过；隔离容器/卷和临时 worktree 均已清理。这只证明该 clean SHA 的 Damai 全旅程通过，不等于 Gate 1全路由响应矩阵完成。

Files:
- Modify only after Gate 1 proves the gap: relevant files under `apps/web/components/dashboard/`, `apps/web/components/statements/`, `apps/web/components/metric-library/`, `apps/web/components/data/`, `apps/web/lib/api/`, `apps/web/e2e/`, and corresponding tests.
- For the approved batch-history subitem only: `services/api/src/flow_api/api/routes/intake.py`, `services/api/src/flow_api/api/schemas/intake.py`, `services/api/src/flow_api/intake/service.py`, `services/api/tests/api/test_intake.py`, `services/api/tests/security/test_route_policy.py`, `docs/40_specs/security/route-inventory-v1.tsv`, and generated OpenAPI/TypeScript contracts. No migrations or changes to persistent demo data.
- For the approved Gate 5 CI database-isolation regression only: `scripts/test_dashboard.sh` and focused `scripts/tests/` coverage. Do not modify `.github/workflows/` or persistent demo data.
- Reuse: `apps/web/lib/deep-links.ts` and `2026-09-26-ui-deep-link-implementation-plan.md`

Acceptance: Gate 1 覆盖表中的每条目标路由都必须逐页通过，不得抽样漏页；对每项覆盖指标/缺失原因同时断言 API 返回与 UI 呈现（正向值和缺失/不适用状态）；页面显示值与 API/源事实一致；点击维度和指标可到达对应记录；数据工作台能看到当前 actor 在当前企业下的历史内部批次与版本；换 actor/企业时不得暴露他人批次；状态与响应式 E2E 通过。

### Gate 5：全链回归并关闭

Run: `make damai-demo-build`
Run: safe isolated dashboard acceptance (must use `flow_test`, never persistent `flow`) and `make test-damai-demo-e2e`
Run: `make lint && make typecheck && make test-web`
Run: `python3 scripts/check_docs.py --phase m1` and the repository link check

验收上述命令、覆盖报告与同 SHA CI 全绿后，更新本工作包、`CURRENT_ROADMAP.md` 和 `PROJECT_STATE.md`。演示 seed/verify 只能在 `test-damai-demo-e2e` 的隔离 Compose 环境中执行；任一 DB 测试必须使用隔离后的 `flow_test`，不得对常驻 `flow` 执行写入或清理。

#### Gate 5 数据库安全前置修正（2026-09-26）

复核发现 `scripts/test_dashboard.sh` 在 pytest 前直接执行 Alembic upgrade 与 `seed_dashboard_demo.py --fresh-batch`；`tests/conftest.py` 的 `flow_test` 自动切换只保护 pytest 进程，不能保护此前的迁移/seed 子进程。已修复为默认且强制数据库名 `flow_test`、主机仅允许 `localhost`/`127.0.0.1`，缺库时只创建固定的 `flow_test`；指向 `flow` 或非本机地址时迁移前拒绝。Next 在本轮临时 web 副本运行，Playwright 从仓库根加载权威配置/fixtures，避免共用 `.next` 锁且不改真实工作区配置。

安全验收：显式把 URL 指向 `flow` 时脚本退出码2并输出拒绝信息；`make test-dashboard` 在 `flow_test` 执行迁移/seed，摘要含12个月/8卡，Playwright 7/7通过。该脚本不再对常驻 `flow` 写入。安全性修复后 Gate 5 dashboard 验收通过；仍须同 SHA CI、页面覆盖矩阵与 Gate 1干净提交证据收尾。

### 快照事实范围与意外测试批次记录（2026-09-26）

- `649a2aba` 令产品表和毛利矩阵按当前快照中的真实事实筛选维度，完整目录仍用于筛选器，覆盖文案显示分子/分母。空事实范围为 `degraded` 并显示明确原因。API 集成测试、Web 全套136/136、typecheck、lint（0 errors，1既有warning）、ruff、mypy通过；隔离大麦旅程 verify 19/19、浏览器 E2E 9/9通过。
- **常驻库写入偏差（未回滚）**：误在根 checkout（旧分支 `codex/damai-logistics-data-audit`，HEAD `4111f6a2`）运行 `make test-dashboard`。该 checkout 的脚本默认指向常驻 `flow`，因此增加已发布测试批次 `01a0dcdd-8245-7c17-99aa-fce91a8a7a57`（2026-09-26 08:38:19 UTC）：1 import、12 metric snapshots、1 analysis run、50,400 metric values。只读检查确认没有删除或覆盖既有记录；该批次改变 latest 选择，当前 API/UI 可能读到测试批次而非原大麦批次。原大麦批次 `01a0dc96-029b-7931-b2b5-4885a3f82132` 仍存在。已冻结常驻库进一步写入；未删除、未恢复数据库、未切换最新批次。任何回滚或切换均待用户明确授权及新备份，后续代理不得自行处理。
- 维度修复验证只使用 `flow_test`/隔离 Compose；常驻库没有在该修复验证中再写入。

### Gate 1 只读端点副作用分类（2026-09-26）

路由实现审查确认客观快照与经营报告渲染类 GET 会直接调用 `freeze_objective_statement_report()` / `freeze_operations_overview()`；冻结函数在当前内容无可复用快照时 `session.add()` 新版本并 `flush()`。因此即使路由 method 为 GET，也不是安全的只读探测目标。上述具体路径已列入 Gate 1 排除清单，其他 endpoint 必须先审查调用链和提交行为，再加入矩阵。后续修正 GET/POST 语义属于独立 API 行为变更，当前仅记录，不在本次只读覆盖批次中擅自修改。

只读矩阵工具已提交为 `0dde935f`：`scripts/damai_visibility_matrix.py` 仅记录方法、路由、状态码、响应字节数、上下文和响应 SHA，不保存正文；失败也会保留矩阵证据。它在隔离全旅程 seed/verify 后、任何页面变更流程前运行，禁止调用上述 freeze/render GET。

干净提交复验（`main@0dde935f`，2026-09-26）：43个不同 GET 请求全部 HTTP 200，无失败；包含 Dashboard 月/YTD、组织/客群/产品/区域各一个维度筛选，两份财报 detail/projection/corrections/workbench/operations，全部7个公开经营期间，指标字典/语义/可计算清单/两个覆盖集，Finding详情，当前企业批次版本与清洗摘要，报告/经营快照发布attempt列表。响应只写 SHA/大小，不存内容；清单摘要 SHA-256 `ab226cd301e0387026b48cdad97eb8eec00f921faf841d320bec296f1523c228bd`。同轮 seed verifier19/19、浏览器E2E9/9。该 SHA 的 GitHub CI run `36241816630`仍在运行。此项关闭“早期矩阵非干净提交且不可复跑”的缺口，不关闭 Gate 1全页面/响应式/加载错误403/深链验收。

### 390px生产构建响应式缺陷修复（2026-09-26）

首次执行生产构建 E2E 门禁时发现 `/data` 批次历史标题/表格导致页面溢出至546px，`/operations` 期间下拉框的长 option 将页面撑至511px。数据页历史区补 `min-width: 0`、标题在窄屏换行，表格限制在自身可横向滚动容器；经营页窄屏选择框固定在容器宽度内，主题网格最小轨道允许缩小。响应式失败诊断保留前20个越界元素，方便定位。

复验：`bash scripts/test_module_boundaries_e2e.sh` 生产构建下69/69通过（含全部导航/页面一致性、11路由390px、4数据页1024/1440、加载/错误/403）；Web Vitest 136/136、`make lint`（0 errors，1既有 TanStack warning）、`make typecheck`通过。全站五态截图归档、所有数据视口、全部深链目标与真实无权限角色链路仍未覆盖。

### 工作台状态可见性补齐（2026-09-26）

- `/data` 批次历史首次读取/刷新期间明确呈现 status；403 与暂时性服务错误分开说明。历史读取不可用不阻断上传工作台，但权限缺失不再伪装为临时错误。
- `/analysis` 工作台请求挂起时的“加载中…”加 `role=status`；已有 error/403 按 `role=alert` 显示。
- 新增 E2E 覆盖数据工作台 loading/403、四问工作台 loading；analysis 加入 error/403矩阵。`bash scripts/test_module_boundaries_e2e.sh` 生产 E2E74/74、Web Vitest138/138、lint0 errors（1既有warning）、typecheck通过。
- 未关闭：所有路由/全部五态的穷举、空/部分降级端到端矩阵，数据密集态跨390/1024/1440覆盖、实际企业角色鉴权、全深链逐项验收。新提交 CI 待完成。

### 空数据态可理解性补齐（2026-09-26）

- `/analysis`：财报列表请求成功但返回空数组时将状态从 idle 转为 ready，显示“尚无可分析的财报”及前往数据接入入口；不把有效空结果无限显示成加载中。
- `/operations`：仅当财报与公开经营期间两个端点都成功返回空集合，显示“暂无可用经营分析数据”、原因和 `/data`、`/public` 两个入口；真实请求失败仍保持错误提示，不伪装为“无数据”。
- TDD 测试先红后绿；生产 E2E76/76、Web Vitest139/139、typecheck通过，lint0 errors/1既有warning。其余页面空/部分降级的逐页状态和三档视口组合仍需覆盖。

### Clean SHA 隔离全旅程验收（`3c15073f`，2026-09-26）

`make test-damai-demo-e2e` 使用专属 `damai-demo-iso` Compose 项目，无页面 mock：迁移与 seed 后 verifier19/19、对象存储读回/sha/语义匹配；只读路由矩阵43/43 HTTP200（本次 manifest SHA-256 `9af6762e888de208f2f0e2d50dd1f057d84a420fe08e7de4b0e69527cc81cccf`）；浏览器旅程9/9（驾驶舱筛选、经营/财报/四问/指标库/Finding审批、报告发布和下载 SHA、数据工作台导入）。写操作仅在隔离数据库与对象存储；脚本退出已清理专属卷，常驻 `flow` 未触碰。GitHub run `36243330055` 仍 queued；其他页面状态-视口全矩阵及深链未关闭。
- 当前 clean SHA `649a2aba` 的 GitHub Actions run `36232029817` success；其后状态同步提交 `7229cd0d` / run `36232204424` 与证据更新提交 `4c55f10e` / run `36232336053` 也 success。旧 runs `36229942486`–`36230243382` 的 dashboard 视觉高度失败发生在 `31a60217` 修复前；`31a60217` run `36230615921` 的 dashboard、integration、intake-e2e、data-contract 及其余 jobs 最终全绿。CI 当前无已知未通过项；Gate 1 页面/视口/错误/403/深链矩阵仍未关闭。

#### CI 环境变量回归（2026-09-26，待修复）

GitHub Actions run `36222136591`（SHA `430020f`）与 `36222489952`（SHA `59b328dc`）的 dashboard job 均在 `make test-dashboard` 入口失败：CI 通用环境把 `DATABASE_URL` 指向 compose 服务库 `/flow`，脚本按 fail-closed 规则拒绝并退出2。拒绝行为正确，但测试作业没有将通用栈 URL 隔离到测试库。下一步只修 `scripts/test_dashboard.sh` 的 CI 测试库选择：CI 优先专用 dashboard 测试 URL，否则强制本机 `flow_test`；本地显式危险 URL 仍须拒绝。不得改 CI workflow，不连接或写常驻库。

验收：新增脚本级回归覆盖 CI 环境注入 `/flow` 与本地显式危险 URL；`make test-dashboard` 本机 7/7；随后最新 main SHA 的 GitHub dashboard job 成功。

## 不做 / 保护边界

- 不重做已关闭的前端一致性 Task 0–9，也不把深链批次一重复记为未完成。
- 不为填满页面将指标字典定义数冒充数据覆盖率；不把不适用指标硬造为适用。
- 不把公开财报 C 级未通过、真实企业授权未取得的状态包装成产品验收通过。
- 不改数据库 schema 或迁移；若 Gate 1 证明必须迁移，先更新路线图与获批规格再另行授权。

## 工作状态

### Gate 5 CI URL 修复更新（2026-09-26）

旧 CI dashboard job 因通用 `DATABASE_URL=/flow` 与数据库安全守卫冲突。现已修复 `scripts/test_dashboard.sh`：CI 优先读取 `FLOW_DASHBOARD_TEST_DATABASE_URL`，否则固定使用 localhost `flow_test`；不继承通用 compose URL。本地显式危险 URL 仍 fail-closed。脚本回归 2/2、本机完整 dashboard 验收（迁移/seed 仅针对 `flow_test`，12个月/8卡，Playwright 7/7）通过。未改 CI workflow，未写常驻 `flow`。提交 `85e907a` 的 GitHub Actions run `36223558441` dashboard job 成功；同一 workflow 其余三个长测仍运行，最终总结果未出。此前根因段落保留为历史记录，以本更新为当前状态。

后续 CI 状态更新：`31a60217` 对应 run `36230615921` 的 dashboard job 已成功（含视觉截图），其余 integration、intake-e2e、data-contract 当时仍运行；完整 workflow 尚未结束。当前维度修复 `649a2aba` 与本工作包/证据文档提交 `7229cd0d` 的 workflow 分别为 run `36232029817`、`36232204424`，均排队中，不能提前标记全 CI 通过。

用户已于2026-09-26批准实施。Gate 1初始诊断绑定 `3ff95115` + dirty overlay；FY2025工作台契约修复、Gate2静态覆盖37/40与40/40、Gate3 OCF以及毛利矩阵比较选择均已完成并推送。OCF隔离验收19/19、E2E9/9；毛利矩阵实际/预算各10/32格可用，缺值不补零。Gate4批次历史接口/页面已在 `430020f` 推送；API+策略18项、组件16项通过，clean SHA `59b328dc` 隔离 Damai seed/verify19/19、E2E9/9。常驻库本轮未访问/写入。当前新发现：两个 GitHub run 的 dashboard job 都因 CI 注入的 `DATABASE_URL=/flow` 与 `flow_test` 安全守卫冲突而失败，待按本 Gate5记录修正测试脚本。完整 Gate1 API响应矩阵、Gate3/4其余缺口/页面与Gate5全链仍未关闭。

本段 CI 冲突描述是修复前快照；以本工作包“Gate 5 CI URL 修复更新”为准：脚本与 dashboard CI 验收已完成，完整 workflow 尚未结束。

### Gate 4 全站深链批次一、二进展（2026-09-26）

全站深链独立计划见[实施计划](../2026-09-26-ui-deep-link-implementation-plan.md)。批次一、二已完成。批次三最新本地实现覆盖：登记公开 PDF 原文服务及 SHA 校验/访问决策审计、财报页码跳原文、按 Finding 批次血缘查看真实源单元格、冻结 objective 新 payload 保留页码/锚点及生成 HTML 回链、管理关注按已有 metric_code 跳指标定义。ManagementWatchItem 没有可证实的 finding_id 关联，因此不造字段或伪链；GET /batches 与批次历史原已实现。当前 Web/E2E/API、本工作包剩余 Gate 1 路由响应矩阵和同一 SHA CI 状态以路线图及深链计划最新更新为准。本工作包仍 active。

批次二提交 `7976691` 推送后，在该代码版本上另跑隔离的大麦全旅程：新 Compose 卷完成迁移与 seed，verify 19/19、浏览器 E2E 9/9。之后为 `/data` 与 `/metric-library` 补充真实数据展示断言：seed 批次必须出现在最近批次表，点击批次名后 `?batch=` 生效且该行标记为当前上下文；指标覆盖矩阵必须显示 FY2025 37/40、FY2026 40/40。两轮新增断言后的隔离全旅程均9/9。证明大麦主演示页面有真实批次与覆盖值展示，并未被深链改动破坏；不代表 Gate 1逐路由覆盖矩阵完成。`7976691` 的 CI run `36225466153` 当时仍在运行，需以最终状态为准。

### 常驻开发库大麦数据恢复（2026-09-26，已执行并复验）

恢复前只读探测发现：health 200；dashboard 返回404 `dashboard_not_ready`；statement reports 2；公开经营期间7；大麦覆盖 FY2025 37/40、FY2026 40/40；operations snapshots 2；publishing snapshots、freeze candidates、findings、intake batches 均为0。判断：静态财报/覆盖数据仍在，日常栈缺少内部经营批次及其分析工作流对象，不能只靠前端下钻修复。

执行结果：先完整备份本机 `flow`，再运行已审查的 `scripts/seed_damai_demo.py` 幂等 seed；未清表、未删除数据、未运行迁移。首轮验收暴露 verifier 把历史财报版本误计入 `statement_report=2` 总行数的问题。已将检查改为只核验大麦 FY2025/FY2026 最新已发布身份，并添加两项 SQLite 回归测试（历史版本不增计数；最新版本未发布则不通过）。随后重复 seed 与验收，关键表计数未增长。最终 `verify_damai_demo.py --api-url http://127.0.0.1:8000 --check-storage` 为19/19；对象存储工作簿读回1,327,348字节且SHA/语义一致。复验 API：dashboard 200、8张KPI卡、趋势12/12、2条 findings，状态 `degraded`；财报2份（FY2025/FY2026），发布快照1、冻结候选12。矩阵仍 `degraded`，缺失值维持 unavailable，不以填零掩盖。

浏览器 `127.0.0.1:3000` 的最初只读 smoke 失败：页面标题可见，但 KPI 卡和财报选项不渲染。Next 日志确认 `allowedDevOrigins` 默认未包含 `127.0.0.1`，内部 JS chunks/HMR 被拦截；Next.js 文档将此配置定义为允许开发资源的额外 host。已在 `apps/web/next.config.ts` 加入该 loopback host。代码变更触发 Next 自身自动重载（本轮未手工停止/启动用户服务）；随后常驻 3000 端口的只读 Playwright 六项通过（Dashboard筛选/API、经营分析、财报、四问、指标库）；另以仅允许 GET/HEAD 的浏览器检查确认 `/data` 显示 `damai-demo-v1`、`/investigations` 显示2条Finding、`/reports` 显示两份年报及经营快照。无页面级 JavaScript 异常。隔离副本完整大麦旅程也通过9/9。现有页面已能显示数据，但正式报告产物历史仍为空，且本组检查不代替Gate 1全路由矩阵和逐页缺口/下钻验收。配置参考：[Next.js `allowedDevOrigins`](https://nextjs.org/docs/app/api-reference/config/next-config-js/allowedDevOrigins)。

此恢复只关闭“常驻开发库数据缺失”这一项，不关闭本工作包任何 Gate；常驻库之外仍只使用隔离栈运行写型 E2E。

### Dashboard 缺失状态可见化（2026-09-26）

全页只读复验发现接口已提供 `status=unavailable` 与 `unavailable_message`，但核心 KPI 比较单元格只渲染 `display_value=—`，用户无法区分未发布与零值。按 TDD 添加组件回归测试，先确认旧实现失败，再在 `MetricGrid` 对 `*_not_published` 显示“未发布”标记；保留破折号表示没有数值，并把接口原因暴露为 `title` 与 `aria-label`。已发布的真实零值仍只显示零，不添加未发布标签。

验证：`apps/web/tests/components/dashboard-deep-links.test.tsx` 10/10、全 Web Vitest 134/134、`pnpm typecheck` 通过、`pnpm lint` 0 errors（保留既有 `flow-data-table.tsx` React Compiler warning）。在常驻 `127.0.0.1:3000`、1440×1000 桌面视口完成 GET-only 浏览器检查：8张卡可见、6个比较项标记未发布、title 为“当前口径未发布该比较值”、无页面级 JS 错误；点击第一张指标卡进入 `/metric-library?focus=orders`。截图在 `/tmp/flow-ui-qa.8ciXBg/dashboard-after.png`（临时证据，不入库）。

遗留：当前比率仍以小数显示（如 `0.108707`），金额/数量精度未做单位化格式审计；这属于下一个显示格式验收项，不把它混入本次状态标签修复。

### 经营分析真实财报缺值与格式修正（2026-09-26）

- 根因：大麦年报的 `bs.current_assets`、`bs.current_liab`、`bs.total_liab`、`bs.total_assets` 是点余额；生成管线可能将其映射为 `cur` 或 `end`。O2 `FACT_DIRECT_CALCS` 仅查询 `cur`，导致已有事实的流动比率、资产负债率错误显示为公式引用未计算。现对点余额同期间允许 `cur → end`，不使用其他期间事实、不改 D01/D02 口径。
- 本机常驻 API GET `/api/v1/operations/overview/01a0dc95-fb0a-7cd8-ab36-5b1a1c95d0ea`（大麦 FY2026）返回 200，最新原始响应体 10,237 bytes，SHA-256 `225a9edbf04ffc0278c378b66f0229a8367b4786479ff0431dbff1a846ed5018`；七项运营效率指标现均可算：流动比率 `0.8119`、资产负债率 `0.8986`、存货周转率 `16.1552`、应收周转率 `3.0931`、应付周转率 `3.9172`、DSO `116.3881` 天、流动资产周转率 `1.9099`。
- 页面按指标 code 展示单位：毛利率/净利率/资产负债率/同比及杜邦结果转为百分比；流动比率与利润现金含量标“倍”；周转次数与天数带单位。百分比/倍数/天数保留两位小数，`title` 提供原始 API 精确值。来源未声明单位的经营披露值保持原样，避免错误四舍五入或假设单位。
- TDD：公式依赖新增测试先红，接通派生指标映射后绿；API 经营引擎 15/15、ruff、mypy通过。前端运营分析组件5/5、Web全套134/134、typecheck通过，lint 0 errors（保留既有 TanStack Table React Compiler warning）。实际常驻 API GET 验证资产负债表余额与 DSO 均恢复为 `computed`；本次未写数据库。
- 页面缺口文案新增 `segment_disclosure_missing` 与 `internal_data_required` 区分断言；先红后绿。Web全套仍134/134，typecheck通过、lint 0 errors（既有warning不变）。
- 未关闭 Gate 1 全路由干净 SHA 矩阵、其他页面全状态/下钻，也未把应收周转天数或内部渠道面板计为已完成。需在本提交 SHA 上继续整体验收与 CI。

### KPI 状态标签视觉回归修复（2026-09-26）

`85a2275` 的 CI 视觉截图因 KPI 状态标记额外形成 CSS Grid 第三行，两个桌面截图页面高度均增加20px。`31a60217` 已将标记收进既有数值行，并新增结构断言。Dashboard 深链10/10、Web Vitest134/134、typecheck、lint（0 errors/1既有warning）通过；隔离大麦旅程 verify19/19、E2E9/9通过。run `36230615921` 的 dashboard job 后续已成功，故该视觉修复通过该 job；该 run 的其他长测当时仍在进行。本机 dashboard 验收因 seed 摘要为 degraded 而提前退出，未执行截图；这条本地命令仍不作为视觉验证证据。Gate 1全站视口矩阵仍未完成。
