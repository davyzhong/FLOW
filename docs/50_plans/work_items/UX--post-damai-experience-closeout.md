---
doc_id: FLOW-WI-UX-POST-DAMAI-001
title: 大麦数据后的剩余体验收口
doc_type: work-item
status: active
version: 3.9
created_at: 2026-09-24
updated_at: 2026-09-26
owner: FLOW
depends_on: [FLOW-WI-DAMAI-FULL-YEAR-001]
acceptance_refs: [FLOW-PLAN-INTEGRATED-EXECUTION-20260924, frontend-route-state-viewport-matrix]
applies_to: web-frontend
---

# 大麦数据后的剩余体验收口

## 目标

让已装载的大麦合成数据在经分专员的核心页面中形成完整、可解释、可下钻的分析体验；明确区分“没有事实”“指标不适用”“快照未发布”“页面未展示”，不以空值补零，也不把静态 sidecar 说成已上线能力。

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

## 实施路线（本文件是规格；实施须按用户已批准的工作状态执行）

### Gate 1：逐页数据链路和缺口归因

盘点驾驶舱、报表分析、指标库、应收/经营分析、报告中心、数据工作台和公开经营分析页，建立“页面 → API → 已发布对象 → 源事实/指标”的覆盖表。每个空白/缺值只能归入：源事实不存在、口径/映射缺失、计算失败、快照未发布、过滤条件不匹配、前端未消费、按设计排除之一，并附可复现证据。

Files:
- Inspect: `apps/web/components/dashboard/`, `apps/web/components/statements/`, `apps/web/components/metric-library/`, `apps/web/components/operations/`, `apps/web/components/reports/`, `apps/web/components/data/`
- Inspect: `services/api/src/flow_api/dashboard/`, relevant statement/metric/operations API routes
- Evidence: add a versioned coverage table to this work item or its linked verification record; do not create another status ledger.

Acceptance: Gate 1 覆盖表必须逐项记录精确路由、请求参数/筛选、公司/组织、期间、数据集/批次、环境标识和 Git SHA；同一环境与 SHA 下冻结脱敏后的 GET 响应摘要或内容哈希。每个目标页有真实 GET 响应证据；缺口均有分类与 owner；已发布但未展示、或页面声称完整但 API 缺值的情况不得留作“无数据”笼统结论。

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

全站深链独立计划见[实施计划](../2026-09-26-ui-deep-link-implementation-plan.md)。批次一、二的代码与本地验收已完成：API/安全用例51/51、Web单测133/133、深链E2E15/15，typecheck、合同生成与文档门禁通过。当前 CI run `36224649915` 的 dashboard 与静态/合同/单测/E2E等已完成作业均成功，但 integration、data-contract、intake-e2e 当时仍运行；此 run 基于 `29877d1`，不能替代当前深链提交 SHA 的 CI 结果。批次三（原文/源记录查看、冻结产物回链、ManagementWatchItem 关联）未开始。Gate 1全路由响应矩阵与本工作包其他页面可见性仍未关闭；因此本工作包继续 active。

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
