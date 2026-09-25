---
doc_id: FLOW-SPEC-DAMAI-DEMO-001
title: 大麦物流全量演示数据发行版设计
doc_type: specification
status: approved
version: 1.5
created_at: 2026-09-24
updated_at: 2026-09-24
owner: FLOW
applies_to: repository
decision_refs: [D052, D053, D054]
knowledge_release: flow-knowledge-2026-09-12.1
---

# 大麦物流全量演示数据发行版设计

## 1. 决策与目标

用户于 2026-09-24 批准“方案 B”：建设 `damai-logistics-demo-v1`，用一套可重复生成、
可一键装载、可自动验收的合成物流企业数据贯通 FLOW 当前所有主要页面，并同步修复审计确认的
CI 文档门禁、状态文档过时和普通启动后无可见演示数据问题。

本发行版不是客户数据，也不是京东物流或菜鸟的仿真披露。它只使用公开材料的规模、业务结构
和合理性区间作为锚，所有实体、交易和解释均为 synthetic。

## 2. 范围

### 2.1 本轮包含

1. 24 个月月度数据：12 个月分析期 + 12 个月上年同期；
2. 大麦物流集团、业务单元、区域、客户、物流产品和管理科目主数据；
3. 经营实际、财务实际、预算、应收账龄、回款与现金相关事实；
4. 两个年度的完整合成财务报告投影，包含利润表、资产负债表、现金流量表、权益变动表和附注索引；
5. 指标快照、AnalysisRun、Finding/Evidence/Conclusion、至少一个可冻结内部报告；
6. 客观财报快照和经营概览快照，使报告中心与财报/经营页面有内容；
7. 确定性生成、manifest、SHA、业务不变量和页面覆盖验收；
8. `make damai-demo-build`、`make damai-demo-seed`、`make damai-demo-verify`、
   `make damai-demo-up`；
9. 修复现有文档元数据门禁并刷新 PROJECT_STATE、路线图、HANDOFF、README/文档导航。

### 2.2 本轮不包含

- 不修改数据库 schema，不新增 Alembic 迁移；
- 不建设日级订单、真实运单轨迹或票级会计流水；
- 不改造当前只支持 actual/budget 的工作簿数据合同；滚动预测仅作为
  版本化 static sidecar 交付，不写入数据库、不计入当前页面覆盖验收；
- 不声称指标库全部条目均可计算；缺少输入的指标保持 unavailable；
- 不部署生产、不写入外部系统；
- 不替代公开财报真实样本与未来授权企业验证。

## 3. 数据画像

### 3.1 时间和规模

- 对比期：2024-09 至 2025-08；
- 分析期：2025-09 至 2026-08；
- 分析期收入目标：人民币 1,050–1,150 亿元；
- 毛利率目标：9%–11%；
- 经营利润保持低个位数利润率，体现物流行业重资产、低利润特征；
- 金额保留 4 位小数，计算全程使用 `Decimal`。

规模锚：菜鸟 FY2025 收入 1,012.72 亿元、调整后 EBITA 3.02 亿元；京东物流 FY2025
收入 2,171.47 亿元、毛利 197.68 亿元。大麦选择更接近菜鸟的收入规模，并以京东物流毛利率
作为护栏，而不是逐项复制两家公司的数字。

### 3.2 业务结构

分析期收入结构目标：

| 业务族 | 目标占比 | 对应产品示例 |
|---|---:|---|
| 国际与跨境物流 | 47.4% | 跨境包裹、国际供应链、海外仓履约 |
| 中国物流 | 46.2% | 国内仓配、供应链、末端配送、冷链 |
| 科技及其他服务 | 6.4% | 物流科技与平台服务 |

允许因月度季节性和舍入产生 ±1 个百分点偏差。设置至少 4 个业务单元、6 个区域、40 个匿名
客户和 8 个物流产品；客户名称不得使用真实客户名称。

### 3.3 可导入粒度合同

“全量数据”不允许只在 profile 里列出维度后，再在 canonical 层压成单个聚合成员。
正式发行包必须满足：

| 数据集 | 受治理粒度 | 最低覆盖 |
|---|---|---:|
| 组织 | 集团 + 业务单元 | 1 + 4 |
| 客户/客群 | 匿名客户 + 客群 | 40 + 4 |
| 产品/区域 | 物流产品 + 区域 | 8 + 6 |
| 经营实际 | 月×客户×活跃产品（组织、区域由主数据映射） | 24 个月且每月覆盖全部维度 |
| 财务实际 | 月×业务单元×管理科目 | 24 个月、4 单元、核心科目齐全 |
| 预算 | 月×业务单元×客群×产品×原始预算行 | 分析期 12 个月、4 单元、4 客群、8 产品、7 类原始行 |
| AR/回款 | 月×客户×5 账龄桶 | 24 个月、40 客户、5 桶，同比期不得缺失 |
| 预测 sidecar | 月×客群×产品 | 分析期 12 个月，不写库 |

预算的 7 类原始行是收入、3 类直接成本、期间费用、经营利润和经营现金流。指标引擎只消费
`REVENUE`/`DIRECT_COST`/`OPERATING_PROFIT`/`OPERATING_CASH_FLOW`：3 类直接成本行共同投影为
`DIRECT_COST`，毛利与毛利率由引擎派生；期间费用作为受治理明细保留并显式记录
coverage gap，不得冒充已支持的预算指标。
具体 canonical 编码为：收入行 `metric_code=REVENUE`；仓储/运输/其他直接成本行保留各自
`management_account_code`，但统一 `metric_code=DIRECT_COST`；期间费用行使用
`metric_code=OPERATING_EXPENSE`；经营利润和经营现金流分别使用同名引擎代码。
预算内部必须逐月/组织/客群/产品满足“收入-三类直接成本-期间费用=经营利润”；
经营现金流预算与经营利润的差额作为显式营运资本/非现金调节记入 manifest 并闭合。

允许使用可解释的稀疏分配，但每个分析月必须覆盖 4 个业务单元、6 个区域、
40 个客户和 8 个产品，不得使用 `DM-AGG` / `P-AGG` / `R-ALL` 代替明细覆盖。

### 3.4 有意植入的分析事件

数据必须包含可由确定性规则发现、且证据能回到源记录的事件：

- 跨境旺季量增但运输单价上升，收入增长、毛利率承压；
- 国内仓配效率改善，单位成本下降；
- 两个大客户回款恶化，31–60/61–90/90+ 账龄上升；
- 某业务单元实际收入低于预算（现有预算合同不含 region 维度）；
- 经营利润与经营现金流短期背离；
- 产品组合变化导致整体单均收入和毛利率变化。

原因只在能由数据证明时写为事实；业务原因保持候选假设或 synthetic 场景说明。

## 4. 技术结构

### 4.1 生成层

新增专用包 `flow_api.fixtures.damai`：

- `profile.py`：公司、期间、规模、业务结构和事件参数；
- `generator.py`：生成 `CanonicalPackage`；
- `statements.py`：从年度内部事实生成闭合的财务报告 payload；
- `validation.py`：业务占比、对账、财务恒等式、账龄和覆盖不变量；
- `manifest.py`：确定性计数、汇总、SHA 与来源说明。

生成器不得读取数据库，不使用随机数或固定随机种子以外的非确定性输入。相同版本必须产生
字节一致的 JSONL/YAML 和语义一致的 XLSX。

### 4.2 静态发行版

`fixtures/damai/` 是生成产物根目录，必须含目录说明：

- `canonical/*.jsonl`；
- `forecast/rolling_forecast.jsonl`；
- `workbooks/damai_logistics_full_v1.xlsx`；
- `statements/damai_fy2025.yaml`、`damai_fy2026.yaml`；
- `manifest.json`；
- `README.md`。

生成产物只能由构建脚本重建，不手工修改。manifest 记录生成器版本、期间、行数、核心汇总、
文件 SHA 和 `synthetic: true`。

### 4.3 装载层

`scripts/seed_damai_demo.py` 负责幂等装载：

1. 复用固定 bootstrap enterprise UUID，将其幂等配置为“大麦物流”，并建立/复用
   一个分析截止月为 `2026-08` 的 AnalysisCycle；AnalysisBatch 只绑定该周期，24 个历史月份
   由 Period/事实表表达，不伪造 12 个无批次归属的周期；整库始终只有一个 enterprise_id；
2. 通过现有 IntakeService 导入并发布标准工作簿；
3. 生成 12 个月指标快照和最新 AnalysisRun；
4. 运行现有 5 个 playbook，将最多 5 个系统 Finding 按真实状态机推进为
   candidate/in_review/approved 混合状态；`submitted` 是从 candidate 进入 in_review 的 decision，
   不是落库状态；
5. 为 approved Finding 写入完整结论并冻结内部报告；
6. 使用独立 synthetic stock code `DAMAI.SYN` 和独立归一化映射导入两个大麦合成财报，
   为每份报告保留非空源 SHA，调用
   `normalize_report`、`ReviewService.publish` 通过质量门禁后，再冻结客观报告和经营概览；
7. 输出机器可读 seed receipt。

脚本不得直接伪造无法通过领域服务验证的发布对象。工作簿和数据库装载仅包含
actual/budget；forecast sidecar 必须携带独立版本、生成时间和 SHA，明确标记
`persistence: static-only` 与 `page_coverage: excluded`，防止将未实现能力冒充为已上线功能。
大麦运营投影也使用独立 `DAMAI.SYN` 静态事实/分部序列，`/operations` 不得读取
`9988.HK` 或任何阿里巴巴经营 fixture。

### 4.4 指标覆盖展示

保留 `p5_metric_coverage_v1.yaml` 作为公开真实财报数据集，另生成
`damai_demo_metric_coverage_v1.yaml`。`/api/v1/metric-library/coverage` 通过受控 `dataset`
参数读取 `public` 或 `damai`，默认值继续为 `public` 以保持向后兼容；前端提供两者
切换，大麦数据集必须显示“合成演示数据”标识，不与真实财报混为同一证据层。

### 4.5 启动与验收

- `make stack-up` 保持空环境/生产语义，不自动灌演示数据；
- `make damai-demo-up` 执行 stack-up 后装载演示发行版；
- `make damai-demo-verify` 校验数据库对象、API 返回和页面依赖，但不修改数据；
- README 明确区分“空环境启动”和“大麦演示启动”。

## 5. 验收合同

### 5.1 数据验收

- 24 个期间严格连续；
- 分析期收入在 1,050–1,150 亿元；
- 三大业务族收入占比在目标 ±1 个百分点；
- 经营收入与财务 REVENUE、经营直接成本与三类财务直接成本逐全量对账通过；
- 每月、每组织 `收入 - 直接成本 = 毛利`，`毛利 - 期间费用 = 经营利润`；
- 预算在每个月/组织/客群/产品粒度满足“收入-三类直接成本-期间费用=经营利润”，
  并有闭合的经营现金流调节表；预算与实际要可比，但不要求数值相等；
- `MetricCalculator` 的 `REVENUE`/`DIRECT_COST` 在 total、organization、customer segment、
  product、segment×product 五种受支持粒度与 manifest 一致；`OPERATING_PROFIT`/
  `OPERATING_CASH_FLOW` 只在其现有合同支持的 total/organization 粒度对账；
  10,752 条细分原始预算保留，但不伪造财务指标尚未支持的细分输出；
  三类直接成本不漏算、不重算；
- AR 五账龄桶合计、到期、逾期、回款均满足非负与定义约束；
- AR 五个账龄桶之和等于应收余额，未到期+逾期等于应收余额，各桶、到期、
  逾期与回款非负，且回款口径与现金流口径有显式调节表；
- 两个年度财务报告满足资产=负债+权益、毛利、净利润归属、现金桥闭合；
- 权益变动表满足期初权益+本期净利润+其他权益变动=期末权益，其期末权益必须等于
  资产负债表权益；现金流量表期末现金必须等于资产负债表货币资金；
- 所有产物 deterministic，第二次构建 `git diff --exit-code fixtures/damai` 为零漂移。
- manifest 中的主数据数量和事实覆盖必须达到 §3.3；profile 声明数量与 canonical
  实际数量不一致时直接阻断发行。

### 5.2 页面与对象验收

| 页面 | 最低验收 |
|---|---|
| `/` | 12 个月趋势、8 个 KPI、产品表、毛利矩阵非空 |
| `/data` | 大麦工作簿可导入，质量与对账通过 |
| `/investigations` | 现有 5 个 playbook 可生成的 Finding 全部可见，含 candidate/in_review/approved 状态 |
| `/reports` | 内部冻结快照、经营快照均可见 |
| `/statements` | 大麦两个年度可切换，三表及扩展章节非空 |
| `/analysis` | 大麦财报四问工作台可返回 |
| `/operations` | 大麦财报经营概览及其独立运营事实有内容；内部 dashboard 由 `/` 验收 |
| `/metric-library` | 字典可见；大麦覆盖只报告真实可算项与结构化缺口 |

`/data` 的验收不以“数据库已有 seed 对象”代替：E2E 必须在页面上上传生成的
XLSX，完成映射、校验、必要的 warning 确认和发布，并断言质量与对账结果。

### 5.3 工程验收

- 新增行为遵循 TDD；
- Python unit、data-contract、metrics、analysis、dashboard、statements、publishing 相关测试全绿；
- Web 单测、lint、typecheck 通过；
- `check_docs.py --phase m6` 通过；
- GitHub Actions 同一 head SHA 全部 required jobs 成功；
- 不新增 migration、不修改 `.env`/CI/CD、不提交真实客户数据。

## 6. 失败和降级

- Docker 不可用时仍可构建并验证静态发行版；数据库 seed/页面验收明确报告为未执行；
- 对象存储或 Chromium 不可用时保留已冻结快照，发布物生成不得冒充成功；
- 某指标缺少事实输入时写入 coverage gap，不以零值补齐；
- 任一财务恒等式或跨表对账失败时 seed 终止，不留下部分提交。
- 第二份财报导入失败、冻结失败或不变量校验失败时，整个 seed 事务回滚；
  重复 seed 不得增长快照、ReviewEvent、冻结版本或源对象计数。
