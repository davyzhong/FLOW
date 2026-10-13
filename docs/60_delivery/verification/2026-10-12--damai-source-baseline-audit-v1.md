---
doc_id: FLOW-VERIFY-DAMAI-SOURCE-BASELINE-20261012-001
title: 大麦物流来源事实与 Mock 基线审计
doc_type: verification
status: draft
version: "1.0"
created_at: 2026-10-12
updated_at: 2026-10-12
owner: FLOW
commit_refs: "[ac45706c]"
evidence_refs: "[damai-fixture-manifest, cainiao-application-proof-sha, alibaba-fy2025-results-sha, alibaba-fy2026-results-sha, source-period-audit, mock-volume-semantic-audit]"
applies_to: damai-demo
supersedes: []
superseded_by: null
---

# 大麦物流来源事实与 Mock 基线审计

## 结论

当前大麦发行包是可确定性重建的 synthetic 测试数据，不是基于已登记阿里/菜鸟公开事实生成的来源驱动数据包。`fixtures/damai/manifest.json` 把 `synthetic` 标为 `true`，但其 `source_ref` 只指向本地 manifest；披露来源、原件 SHA、页面定位、转换输入和聚合核对没有进入数据血缘。报表、运营序列、预算与交互明细目前不能作为菜鸟历史经营事实展示。

来源审计确认有足以支撑第一批历史数据的原始材料，但每类披露的粒度、准则、期间不同，不能强行拼成一套菜鸟完整年度实际账。下一阶段须以披露范围为上限：可定位的报告值进入事实层，纯计算结果进入派生层，未披露的明细只作为带标识、可聚合对账的演示生成数据，无法从来源复算的指标显示 unavailable。

## 可用原始来源与可用范围

| 来源 ID | 仓库原件及 SHA-256 | 原始披露锚点 | 可用范围与限制 |
|---|---|---|---|
| `CNAI-IPO-2023` | [`Cainiao_application_proof_20230926.pdf`](../../knowledge-base/02_research/original/p5_samples/cainiao_private/Cainiao_application_proof_20230926.pdf)；`3e2c367958eacf3bb50c165204a1093383381f5cdb9d8af506636b880b54b13c`；[公开申请稿镜像](https://www.stattimes.com/pdf_upload/cianio272-55784.pdf) | PwC 会计师报告的历史财务信息：PDF 物理页 464 / 印刷页 I-5，单位 RMB'000，FY2021–FY2023；业务线收入：物理页 363 / 印刷页 354；国际物流件量及中国物流订单披露见印刷页 246、253 | 可提供 FY2021–FY2023 全套合并财务报表、现金流、权益变动及部分经营指标。申请稿明确标为 draft，且 IPO 后撤回，必须保留“申请版本/历史期间”身份；不得说成菜鸟已上市后的最新年报。 |
| `BABA-FY2025-RESULTS` | [`BABA_FY2025_annual_results.pdf`](../../knowledge-base/02_research/original/p5_samples/alibaba_9988/BABA_FY2025_annual_results.pdf)；`1620286e40fb7ed9d17f6de2608aea8922eeaf2c446542d0ae2639563cfc2986`；[港交所原件](https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0515/2025051500870_c.pdf) | FY2025 年度业绩公告物理页 18–21：菜鸟 FY2024/FY2025 分部收入 RMB99,020m / RMB101,272m；经调整 EBITA RMB1,402m / RMB302m | 支持 FY2024–FY2025 分部趋势锚点，不含菜鸟独立的完整资产负债表、现金流量表和完整损益表。年度业绩公告说明其为未审计初步信息；需优先以正式 FY2025 Form 20-F 复核并作为终版财务来源。 |
| `BABA-FY2026-RESULTS` | [`BABA_FY2026_annual_results.pdf`](../../knowledge-base/02_research/original/p5_samples/alibaba_9988/BABA_FY2026_annual_results.pdf)；`e264c45dbc7e6fd039cc4a948557a4e55f7df9a1889b134cbc3fdf1a9a265b9e`；[港交所原件](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0513/2026051300654_c.pdf) | FY2026 年度业绩公告物理页 18–21：报告架构说明菜鸟已重分类进“所有其他”；FY2026 表列“所有其他”汇总数，脚注将菜鸟与盒马、阿里健康、高德等合列 | 不能从“所有其他”汇总值反推菜鸟单体或分部值；FY2026 菜鸟单独财务数字应为 unavailable。正式报告的报告分部边界亦见[阿里 FY2026 Form 20-F](https://www.sec.gov/Archives/edgar/data/1577552/000119312526231755/baba-20260331.htm)。 |
| `CNAI-FY2024-OPS` | [菜鸟官方介绍](https://www.alibabagroup.com/en-US/document-1747836787297878016)；[阿里 FY2024 年报菜鸟业务介绍](https://static.alibabagroup.com/reports/fy2024/ar/ebook/EN/34/index.html) | 菜鸟披露 FY2024 跨境及国际包裹日均量超过 500 万 | 这是下限描述，不是精确包裹总量；不能将“超过 500 万”改写成精确值，也不能据此声称客户、月度、区域或产品线实际值。 |

原件文件摘要与校验来源见样本档案说明 [`p5_samples/README.md`](../../knowledge-base/02_research/original/p5_samples/README.md)。原件未作修改。

申请稿 I-5 的原始损益表列 FY2021/FY2022/FY2023 收入分别为 RMB52,732,812k、RMB66,866,916k、RMB77,799,675k，毛利分别为 RMB5,543,738k、RMB7,180,629k、RMB8,146,656k，净亏损分别为 RMB2,015,187k、RMB2,285,665k、RMB2,801,391k；这些是原文值，不是当前 synthetic 包的推算值。完整源值及逐行锚点将在机器可读来源登记中记录，避免把此摘要当作源台账。

## 已有可复用来源数据与实现

仓库已有一套菜鸟公开数据抽取结果，不应再造一份重复的事实源：

| 已有资产 | 作用 | 接入现状与缺口 |
|---|---|---|
| `docs/implementation/p5/cainiao_2021fy_statements.yaml`、`cainiao_2022fy_statements.yaml`、`cainiao_2023fy_statements.yaml` | 来源申请稿历史信息的三年完整财务报表行 | 由 `scripts/p5_extract_cainiao.py` 维护；含原件路径、人民币千元原值。需要给每条 facts 补齐报告 SHA、PDF 物理页/印刷页、表/行定位和标准 ID。 |
| `docs/implementation/p5/cainiao_operating_metrics.yaml` | FY2021–FY2023 运营量、业务线收入占比、FY2023 公开非 IFRS 指标与网络快照 | 已包括源 PDF SHA 前缀和披露页码；FY2023 为 1,519 百万国际件、2,311 百万国内物流订单，FY2024 申请稿 stub 为未经审计。 |
| `docs/implementation/p5/cainiao_segment_series.yaml` | 阿里 FY2019–FY2025 菜鸟分部收入与披露的经调整 EBITA | 已如实缺省未披露的 EBITA；FY2026 进入“所有其他”后不含菜鸟单体数据。由 `services/api/src/flow_api/operations/engine.py` 的 CAINIAO 来源路径读取。 |
| `scripts/p5_extract_cainiao.py` 与 `services/api/src/flow_api/operations/engine.py` | 抽取和公开运营数据加载实现 | 可复用抽取器、序列及源文件路径。当前大麦生成路径使用独立 synthetic 计算器，所以不会自动继承 CAINIAO 的披露值。 |

最直接的实现方向是把这些现有来源资产作为 `大麦物流` 演示发行的披露事实输入，通过事实 ID 引用，不重复抄录或改写原始值；未披露的月份、客户、产品和组织切片另建明确的生成明细层。该复用仍须补全逐值血缘和隔离展示，不能直接把 CAINIAO 法定主体名称改成大麦并声称为同一企业。

样本档案 `README.md` 有一句将分部重分类写为“FY2027 起”，与 FY2026 年度公告/20-F 的报告架构及 `cainiao_segment_series.yaml` 当前注释不一致。该 README 位于原始档案树，按不可变档案规则不原地改写；正式源登记中须追加一条更正记录，并给 README 的既有错误加醒目 errata 指针。

## 当前发行包与公开来源的断层

| 现有数据/口径 | 审计证据 | 处置要求 |
|---|---|---|
| FY2025 / FY2026 财务报表 | 两个期间是 2024-09 至 2025-08、2025-09 至 2026-08；阿里/菜鸟财年截止 3 月 31 日。报表注明 CAS 简化 synthetic 投影，没有官方科目逐行映射 | 不标为菜鸟实际年度财报；后续改用来源明确的财年/期间。FY2024–FY2025 只可使用已披露分部指标；FY2026 单体数值不可用时标 unavailable。 |
| 分部收入与 EBITA | 现值 FY2025 RMB94,307.9096m / RMB10,014.3134m，FY2026 RMB111,283.3333m / RMB11,819.3093m，来源都只是 manifest。FY2025 公开值为 RMB101,272m / RMB302m，但财年范围也不相同 | 移除事实展示语义；以源登记值重建支持的期间。不能把现值包装成报告期实际或由公开值直接复算的分部数。 |
| 运营件量 | FY2025 国际包裹 `0.075 百万件`、中国履约量 `0.0721 百万件`；但公开材料分别披露 FY2023 国际物流件量 1,519 百万件、中国物流订单 2,311 百万单。当前序列只由营收除以“每单 120 万元”再乘件单比例得到，且 `china_orders_fulfilled` 字段实际也是件量公式 | 该口径存在严重数量级与字段语义问题，必须重建。公开披露仅提供其自身期间与口径；不把跨年值冒充同期间核对基准。 |
| 业务线收入占比 | 当前 46.03% / 47.56% / 6.40% 从 synthetic 月度事实计算，不能当作菜鸟公开分部实际。申请稿 FY2023 的三个业务线金额可定位，但不等于 FY2025/FY2026 结构 | 只将公开原件明确披露的历史组合进入事实层；其他期间不延用历史占比作为事实。 |
| 利息、折旧、负债及现金流细项 | 利息是财务费用 65% 拆分；折旧按固定资产年率 10%估算；债务/应付、销售收现、资本开支为合成展示拆分 | 有来源明细才进入披露事实；可从真实披露项严格复算者进入派生层；其余隔离为演示数据或 unavailable。 |
| 业务组织、客户、产品、预算、应收与账龄 | 40 客户、4 业务单元、6 区域、8 产品等由确定性生成器创建；预算系数、应收账龄比例和 planted events 为显式生成参数 | 只能保留为隔离的演示/测试明细，且各页面显著标识；不得把它们命名为真实客户、真实组织、真实预算或实际账龄。 |

## 当前来源门禁判断

- 可用于完整三表历史事实的最细年期：菜鸟申请稿中的 FY2021–FY2023，IFRS，人民币千元，逐行原件可复核；其草稿/撤回身份必须随数据展示。
- 可用于更新分部趋势的年期：阿里 FY2024–FY2025 菜鸟收入与经调整 EBITA；不能据此构造菜鸟完整三表。FY2025 终版数须用 FY2025 Form 20-F 复核。
- FY2026 起菜鸟已合并披露至“所有其他”，报告未单列菜鸟，不能从混合组总数分摊出单体事实。
- 现有 P5 菜鸟来源值、抽取器与公开运营加载实现可复用；当前问题是它们尚未驱动 `DAMAI.SYN` 的财务/经营演示包，也没有逐值来源锚点，不是缺少重做另一份菜鸟事实清单的理由。
- FY2024 运营量为“日均超过 500 万”的下限披露；精确月度/客户/区域/产品分配均未公开。
- 当前 FY2025/FY2026 发行包**未通过来源事实门禁**。这份记录仅为首轮基线审计，尚未替换数据、完成 source-fact registry、转化规则和完整图表映射；不得据此宣布新数据包验收通过。

## 下一步

在该单一队首中建立机器可读来源登记，先核实 FY2025 正式 Form 20-F 与菜鸟申请稿的科目映射；再确定采用的报告期间及其会计准则，不把 IFRS 源行机械映射成 CAS。生成的下钻明细须采用可复现的显式分配规则、保留源事实 ID，并按源期间聚合核对；预算、客户和组织只能处于测试/演示层。完成全量字段、50 个指标与 51 图表映射后，再修改生成器和 UI。

本轮为只读来源与数据语义审计；未写数据库，未修改或替换任何原始 PDF。
