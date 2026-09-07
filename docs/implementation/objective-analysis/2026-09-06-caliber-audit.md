# C01 来源与专业口径核验（指标库 v1 + 会计基础 v1）

- 核验日期：2026-09-06；核验人：Kimi（接手 Agent）
- 对象：`config/metrics/metric_dictionary_v1.yaml`（55 指标）、`config/metrics/accounting_foundation_v1.yaml`（167 科目 / 48 准则 / 32 分录模板）
- 依据：D047 默认推荐策略；调研资料 07–11 号（`docs/knowledge-base/02_research/original/`）
- 方法：逐项核对 provenance/caliber/适用条件字段是否可定位到权威来源；研究摘要仅作线索，不作权威依据

## 1. 指标字典核验（55 项）

### 1.1 字段完整性（机器核验）

| 检查 | 结果 |
| --- | --- |
| 全部指标有 provenance（来源） | 55/55 通过 |
| 全部指标有 caliber（口径说明） | 55/55 通过 |
| v1 定稿字段（default_caliber / alternative_calibers / default_basis） | 齐备（D047「默认口径 + 备选并存」落地） |
| MPM 指标带 reconciliation（调节关系） | 7/7 通过（ebitda、adjusted_ebitda、ebitda_margin、free_cash_flow、direct_cost、operating_profit、collection_rate） |
| benchmark 覆盖 | 40 通用指标齐备；15 物流行业指标无基准（企业内部经营指标，无公开基准属预期，如实保留空缺） |

### 1.2 来源分层

- **准则/权威来源**（调研 10 号逐项验证）：CAS 科目体系（财政部 2006 附录 + 2024 汇编）、国资委 22 项绩效评价指标逐项公式、CPA 教材口径与管理用报表推导链——偿债/营运/盈利/现金流指标的主口径依据；
- **行业惯例与研究梳理**（调研 07–09 号）：四大方法论、评级机构口径、杜邦体系——作为结构与备选口径依据；
- **工程契约**：15 个物流指标迁移自 `flow.metrics.logistics.v1`（`migrates_from` 留痕），其口径即 V1 已冻结契约。

### 1.3 待核与保留事项（不阻塞 C01，进入 C02 时携带）

| 项 | 说明 | 处理 |
| --- | --- | --- |
| 经验阈值类 benchmark | 「流动比率约 2」等为教科书/行业惯例，非法规阈值 | 口径卡保留来源标注；不进入任何硬性判定 |
| 准则有效期 | CAS 14/21/22（2017–2018 修订）现行有效；IFRS 18 将于 2027 年生效 | 准则登记册已含 note；IFRS 18 相关口径在 2027 前为「提前参照」标记 |
| MPM 边界 | 企业自定义指标（Non-IFRS）不一律等同 IFRS 18 MPM | 已按 D049 单列 `mpm` 标记 + reconciliation 必填 |

## 2. 会计基础数据核验（167 科目 / 48 准则 / 32 分录模板）

| 检查 | 结果 |
| --- | --- |
| 科目构成 | 2006 附录 156 + 2024 演进新增：current 157 / added_2024 10，六大类（资产 74 / 负债 37 / 损益 36 / 权益 8 / 成本 7 / 共同 5） |
| 准则登记册 | 48 项（CAS 具体准则 + 基本准则 + IFRS/IAS），issuer 与要点齐备 |
| 分录模板 | 32 个物流业务场景，related_metrics 与指标库建立映射链 |
| 已知缺口（如实保留） | 171 科目体系正式编号以《应用指南汇编 2024》正式出版物为准；使用权资产 1802 / 租赁负债 2703 为实务通行编号，待原文核对后版本化修订 |

## 3. 原审计结论（2026-09-06 时点；以下结论不等于完整口径正确性认证）

- 来源可定位性与适用条件：**通过**。全部启用项可定位到权威来源或明确标注为工程契约/行业惯例；不确定项已显式标记（本表 §1.3、§2 缺口），无「以研究摘要冒充权威来源」项；
- C01 完成标准满足；遗留待核项进入 C02（可执行定义绑定）时随版本化变更流程处理。

## 4. 2026-09-07 订正说明

上表 `MPM 7/7` 证明当时标记项目存在调节字段，不能证明 IFRS 18 分类正确。FCF、单独比率等仍存在误标，参[参考总册 C02–C05](../../knowledge-base/02_research/synthesis/2026-09-07-reference-and-improvement-master.md)。因此“来源字段齐备”“可定位”“内容已核实”“可执行”必须分别验收。C01 的历史交付保留，新一轮来源/分类订正进入 P01，不因本次文档解释宣称配置已修。

## 5. P01 订正实施记录（2026-09-07）

**C02（MPM 分类）：已实施，语义订正非文案改动。**

- 原状态：7 条指标带裸布尔 `mpm: true`（ebitda、adjusted_ebitda、ebitda_margin、free_cash_flow、direct_cost、operating_profit、collection_rate），把"管理常用"与"IFRS 18 监管定义 MPM"混为一谈。
- 新语义（`flow_api/metrics/mpm_semantics.py` + 迁移 0019 新增 `mpm_review` JSONB 列，前向默认 NULL=未核验，不伪造历史）：
  - `mpm: true` 为监管级断言，必须携带 `mpm_review{determination: verified_applicable, verified: true, basis}`，否则数据无效；
  - 管理常用指标只允许 `determination: candidate`（是否属 MPM 依公司实际财报逐例判定）；
  - 准则定义小计 / 成本口径 / 内部经营指标 `determination: not_applicable` 或 `management_caliber`。
- 七条逐项判定（均改为 `mpm: false`）：
  | 指标 | 判定 | 依据 |
  | --- | --- | --- |
  | free_cash_flow | candidate | IFRS 18（IASB 2024-05 发布，2027-01-01 生效）B116–B118；EY/KPMG 指引（提前参照） |
  | ebitda / adjusted_ebitda / ebitda_margin | candidate | 同上；adjusted_ebitda 另注 IFRS 18.B116–B117 |
  | operating_profit | management_caliber | FLOW V1 工程契约；管理口径合计须调节至 CAS 营业利润法定行项目（财会〔2018〕15 号） |
  | direct_cost | not_applicable | 成本会计口径，非业绩指标列报 |
  | collection_rate | not_applicable | 内部经营指标，不在法定财报列报 |
- 不变量已在导入器强制（加载即拒绝违规配置），守护测试 `tests/metrics/test_mpm_classification.py`（7 项，含负净利净现比降级与别名同身份）。

**C03（EBITDA/FCF 当现金）：已实施。** ebitda、free_cash_flow 口径说明补"不是现金流量表定义的现金，禁止与货币资金或经营活动现金流量净额混称"。

**C04（营业利润公式简化）：已实施。** operating_profit 口径注明"不得简化为营业收入−营业成本"，法定形成关系依财会〔2018〕15 号，调节要求保留。

**C18（调整后利润）：已实施。** adjusted_ebitda 口径注明"不得与法定利润混同，展示必须带'调整后 / Non-GAAP'标签并引用调节表"。

**C05（净债务）：盘点结论——本库不收录净债务指标。** 如未来收录，默认口径为**有息债务（短期借款 + 一年内到期的非流动负债 + 长期借款 + 应付债券 + 租赁负债）− 现金及现金等价物**；备选口径（含/不含租赁负债）并存记录；禁止"总负债 − 现金"简化口径进入任何展示。

**I08（费用率）：盘点结论——派生展示，不新增定义。** 期间费用率（销售/管理/研发/财务费用 ÷ 营业收入）为派生比率，分子科目已映射（is.selling_exp 6601、is.admin_exp 6602、is.fin_exp 6603）；**缺口：is.rnd_exp（研发费用）无科目映射**（研发费用在 2024 汇编中的列报口径待原文核对），进入 P02 报表映射增量；报告层费用率展示由派生计算承担，不新增静态指标定义。

**C01（净现比复用）：确认。** `ocf_net_profit_ratio` 在册（名称"盈利现金比率"、单位倍、口径注明负净利润失真降级）；本日渲染层 KPI 补齐同规则：净利润为负时显示"—（净利润为负）"而非绝对值。
