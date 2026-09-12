---
doc_id: FLOW-NAV-LEGACY-0706
title: next-stage-baseline
doc_type: navigation
status: current
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
applies_to: docs
---

# 下一阶段工程基线与差异登记（P00）

## 0. 基线刷新（2026-09-07，执行前校准）

- 代码基线：`9e4e04f`（main，与 origin/main 同步）；自 `65345ff` 以来的增量：
  `006dbba`（P00 登记）、`fbb6797` + `9a52eac`（客观报告 PDF 交付·格式评审草稿）、
  `5c221e3` + `c3269fd`（v3 富报告：matplotlib 图表 + KPI 卡 + 多章节，含并行会话提交）、
  `9e4e04f`（v3 渲染器契约收尾：章节对齐测试契约、附录取数修复、杜邦三因子 HTML 文本、
  lint/mypy 全绿）。
- CI：`fbb6797`/`9a52eac`/`5c221e3`/`c3269fd` 四个提交 **failure**（v3 契约测试 3 项失败 +
  lint/mypy 错误，正是渲染器未完成契约所致）；`9e4e04f` **success**（run 34102380687，
  本地另验证：CI 单元选择器 347 通过、mypy 145 文件无错误）。
- 工作树：本次刷新时点已跟踪文件无修改（`var/metric_library_audit.jsonl` 为运行时审计
  产物，不属于源码差异）。
- C10 留出冻结进展：**组合满足性达成**——holdouts = tencent_fy2025（新期间）+
  sf_2026h1（新期间，2026-09-07 登记冻结）+ zto_2026q1（新公司，2026-09-07 自港交所
  披露易下载冻结，SHA-256 与校验记录见 manifest）；yto_2026q1 移入 `regression:` 段。
  逐行 oracle 答案仍待独立录入者（见第 5 节未知 5，仍为 I03 验收阻塞项）。
- I08 证据更新（显示层）：v3 渲染器现输出净现比 KPI 卡、盈利比率表「净现比（经营现金流
  ÷归母净利润）」行与毛利率行（`objective_report_html.py`，tests/statements 契约守护）；
  定义在册（C01），执行绑定与费用率分子科目盘点仍待 P01。
- 本文件其余章节（第 1–5 节）为 2026-09-04 登记内容，按登记纪律原样保留；
  与上述刷新冲突之处以本节为准。

## 0.1 P01 + P02 实施记录（2026-09-07，接 §0 刷新）

**P01（00e5655）**：C02 已实施——MPM 语义重构（`metrics/mpm_semantics.py` + 迁移 0019
`mpm_review` JSONB，前向 NULL=未核验；七条 `mpm: true` 全部改 false 并逐项判定：
FCF/EBITDA 家族 candidate、operating_profit management_caliber、direct_cost/
collection_rate not_applicable），导入器加载即强制不变量；C03/C04/C18 术语订正随
YAML 条目落地；C01 净现比复用确认（单位倍）+ 渲染层负净利降级；别名 resolver
（`metric_library_store/search.py`）；I08 盘点完成——费用率定为派生展示不新增定义，
is.rnd_exp 缺科目映射登记进 P02；C05 盘点结论——净债务不收录，未来默认口径=
有息债务−现金及现金等价物。守护测试 `tests/metrics/test_mpm_classification.py`。

**P02（本提交）**：I06/I14 已实现（合同层）——`config/analysis/objective_topics_v1.yaml`
+ `analysis/topics.py`：四问（增长/利润/资金/现金）× 七专题（六专题 + 横向偿债风险）
多对多映射，主题合同含 topic_id/metric_refs/required_facts/allowed_grains/
comparison_modes/unavailable_reasons；I07 已实现——essential 十指标默认子集（每项带
替代与不可用条件，元数据标记不缩减词典）；I15/C16/C17 已实现（合同层）——
`metrics/comparison_contract.py`：币种/范围/期间/重述/存量流量五类类型化不可比原因 +
预算完成率守卫（无版本/粒度不匹配/零负预算均类型化拒绝）；C09/C11 已实现（合同层）——
账龄披露层与客户下钻按可用性禁用规则入主题合同；`metric_library_store/coverage.py`
四层覆盖率（登记/可执行/源数据覆盖/展示启用分层蕴含、逐指标行 + 分层 summary）。
对应行状态更新：I06 缺口→合同层已实现（展示层待 P07）；I07 部分→合同层完成；
I13 缺口→合同规则落地（样本级记录待 P04）；I14 缺口→合同层已实现；
I15 部分→比较合同落地（同行比较前提待 P04+）；C09/C11/C16/C17 待修→合同层落地。
守护测试 `tests/analysis/test_topic_contracts.py`（12 项）、
`tests/metrics/test_coverage_layers.py`（3 项）。

---

- 登记日期：2026-09-04（执行 P00 时点）；登记人：FLOW 会话（机器可核验部分）
- 代码基线：`65345ff`（main，与 origin/main 同步；基线核验起点 `22061da`）
- 数据库迁移头：`0018_metric_governance`
- 工作树：已跟踪文件无修改；根目录无遗留未跟踪归档（7 个归档文件已随另一机器的
  治理轮入库，本地冗余副本经哈希比对一致后清除）
- CI：`8c7dbf3`、`0554dca` 已验证 success；`65345ff` 及后续以
  [GitHub Actions](https://github.com/davyzhong/FLOW/actions) 实时结果为准
- 上游输入：[A01 基线审计](2026-09-06-baseline-audit.md)、
  [参考与订正总册](../../knowledge-base/02_research/synthesis/2026-09-07-reference-and-improvement-master.md)、
  [验证清单 manifest](../../../validation/financial_reports/manifest.yaml)、
  [P00–P12 计划](../../90_archive/plans/2026-09-07-next-stage-upgrade-plan.md)

## 1. 实现状态分层（回答 C11：四层分开计数）

| 层 | 口径 | 当前证据 |
| --- | --- | --- |
| 知识条目（登记） | 55 财务指标 + 43 经营指标 | `config/metrics/metric_dictionary_v1.yaml`、`operations_dictionary_v1.yaml` |
| 执行绑定（可算） | 指标 → 事实/分录绑定 | `metric_library_store/binding.py`；C02 的 15/40 与后续 16/39 为版本时点数 |
| 源数据覆盖 | 抽取/导入是否提供必要事实 | B01–B05；逐指标覆盖表待 P02 |
| 结果展示 | UI 卡片/图表/报告引用 | `/metric-library`、`/reports`；经营轨只读 |

> 四层分别计数，禁止把"登记 55 条"表述为"55 条可算/可展示"。

## 2. I01–I30 逐条登记（30 项建议）

状态取值：已实现 / 部分（有底座待验收或待扩展）/ 缺口（未开始）/ 不适用（本阶段）。
"差异/回归路径"为该建议落地时必须新建或回归的内容。

| 项 | 建议摘要 | 状态 | 证据 / 差异与回归路径 | 负责人 |
| --- | --- | --- | --- | --- |
| I01 | 来源/访问/可信度/版本统一账本 | 部分 | `validation/financial_reports/manifest.yaml` + 本目录审计文档已登记账本；统一"来源账本"产品结构未建 | 技术负责人（P01 补来源字段） |
| I02 | 原件/层级/小计/清洗轨迹 | 部分 | B02 抽取器 + `SourceRecord` 字段级血缘（0011/0005 迁移）；独立全行 diff 待 P05 | 技术负责人 |
| I03 | 独立逐行答案与未污染留出 | **缺口（最高风险）** | [oracle-register.md](../../../validation/financial_reports/oracle-register.md)（本 P00 新建框架）；逐行录入待独立录入者 | 独立财务复核者 |
| I04 | 会计知识/计算合同分层 | 已实现 | `accounting_foundation_v1.yaml`（167 科目/48 准则/32 分录）；D040/D048 | 技术负责人 |
| I05 | MPM、FCF、利润、净债务订正 | 缺口 | C02–C05 逐条待修（见订正登记表）；`free_cash_flow.mpm: true` 待版本化订正 | 财务口径负责人 |
| I06 | 四问默认阅读路线 | 缺口 | 四问→指标映射待 P02 定义 | 产品 |
| I07 | 十指标默认子集 | 部分 | D01 `objective_finance_v1.yaml` 11 条目（复用前按 CI 核验）；展示配置待 P02 | 产品+技术 |
| I08 | 费用率与净现比接通 | 部分 | `ocf_net_profit_ratio` 已存在（名称"盈利现金比率"、单位倍、负利润降级）；费用率分子科目盘点待 P01 | 财务口径负责人 |
| I09 | 应收与收入增速联看 | 缺口 | 期间对齐与信号提示待 P03 | 技术 |
| I10 | 毛利率结构/组合拆解 | 部分 | Phase 5 物流毛利桥可复用守恒模式；同粒度量价拆解待 P03 | 技术 |
| I11 | 利润层次/扣非/调整项 | 缺口 | 只用披露口径并登记调节证据，待 P01/P03 | 财务口径负责人 |
| I12 | ROE 分母与现金适用提示 | 缺口 | 适用条件与反例测试待 P03 | 技术 |
| I13 | 账龄/库存/经营效率 | 缺口 | 按披露可用性逐样本记录，待 P02 | 产品+技术 |
| I14 | 六专题与横向现金/偿债 | 缺口 | 专题映射待 P02 | 产品 |
| I15 | 同比/预算/累计/同行比较合同 | 部分 | `metrics/comparisons.py` 底座；不可比阻断合同待 P02/P03 | 技术 |
| I16 | 下钻与驱动拆解分开 | 部分 | Phase 5 Driver 模式；颗粒度守恒前置待 P03 | 技术 |
| I17 | 同快照图表与证据明细 | 部分 | 不可变快照身份（Phase 4）；同源投影待 P04 | 技术 |
| I18 | 报告→差距→解释→决策请求 | 缺口 | 客观/主观分层待 P06 | 产品 |
| I19 | 事实报告不强制主观 Finding | 缺口 | P06 主线待完成 | 技术+产品 |
| I20 | 统一冻结载荷多格式一致 | 部分 | Phase 9 四格式同快照；客观载荷扩展待 P08 | 技术 |
| I21 | 主数据实体/组织/有效期 | 不适用（本阶段） | P12 内部试点前置 | - |
| I22 | 业财链路与对账 | 不适用（本阶段） | P12 | - |
| I23 | 六经营域/八维度/权限 | 不适用（本阶段） | P12 | - |
| I24 | OEE 等行业模型 | 不适用（本阶段） | P12 | - |
| I25 | 13 周现金预测 | 不适用（本阶段） | P12 | - |
| I26 | Issue/Action 闭环 | 不适用（本阶段） | P12 | - |
| I27 | AI 只辅助解释 | 部分 | Phase 8 Copilot 门禁回归 + P06/P09 扩展 | 技术 |
| I28 | 旧缺陷回归集 | 部分 | 本文件第 4 节登记已修缺陷清单；P09 回归用例待建 | 技术 |
| I29 | 真实存储/PDF/备份恢复 | 部分 | S3 根因已修（2026-09-06）；真 PDF 打印、备份恢复待 P08–P11 | 技术 |
| I30 | 单一当前状态与变更追踪 | 已实现 | PROJECT_STATE 2026-09-07 重构（当前页+历史快照）；执行前校准即本文件 | 全体 |

## 3. C01–C18 逐条登记（18 项订正）

| 项 | 订正摘要 | 状态 | 处置路径 / 证据 |
| --- | --- | --- | --- |
| C01 | 净现比应"新增"实为已存在 | 已核对 | `ocf_net_profit_ratio` 在册（配置约 1060 行起）；P01 检查别名/绑定/显示覆盖 |
| C02 | FCF/非财务指标误标 IFRS 18 MPM | **待修** | `free_cash_flow.mpm: true` 需版本化订正；分开管理口径与监管 MPM（P01） |
| C03 | EBITDA/FCF 当现金利润 | **待修** | 形成关系术语修订（P01/P03） |
| C04 | 营业利润公式简化 | **待修** | 法定形成关系/管理变体/调节分别登记（P01/P03） |
| C05 | 净债务=总负债−现金 | **待修** | 引入口径与适用标签（P01） |
| C06 | 比率同向/阈值普适 | 待修 | 适用条件与提示（P03） |
| C07 | CAGR 间隔数混淆 | 待修 | 固定间隔定义与反例（P03） |
| C08 | 驱动路径直接加总 | 待修 | 守恒测试与残差展示（P03） |
| C09 | 公开财报无账龄明细一刀切 | 待修 | 按样本披露可用性记录（P02/P04） |
| C10 | 有文件=独立留出 | **本 P00 处置** | [oracle-register.md](../../../validation/financial_reports/oracle-register.md)：锁独立逐行答案、圆通移为回归集、登记未污染候选 |
| C11 | 55 指标=55 可算 | **本 P00 处置** | 第 1 节四层覆盖表 |
| C12 | 素材/科目计数口径混用 | **本 P00 处置** | 来源目录保留分母与时间（167 科目以 `accounting_foundation_v1.yaml` 当前索引为准） |
| C13 | 网页/截图/wiki 视为已核验 | **本 P00 处置** | 证据等级=已访问原文/截图/派生解释三档；oracle 登记仅接受原文 |
| C14 | 相关性=原因 | 待修 | 事实/信号/假设分离（P03/P12） |
| C15 | 旧修复重报为新功能 | **已校准** | A01 基线审计（2026-09-06）已解决：WS0–4 抽查属实、S3 已修记录保留 |
| C16 | 单月/累计/期末直接比较 | 待修 | 期间/存量流量对齐契约（P02/P03） |
| C17 | 预算完成率统一套用 | 待修 | 差额/方向/比率分开（P02/P03） |
| C18 | 调整后利润=法定利润 | 待修 | 标签/调节/不可用原因（P01/P03） |

## 4. 已修复缺陷回归清单（I28，供 P09）

| 缺陷 | 修复提交 | 回归守护 |
| --- | --- | --- |
| S3 代理根因（系统代理劫持+超时） | 2026-09-06 `infrastructure/s3_client.py` | F01 部署回归 |
| 汇总仪表盘 `request.text()` 损坏 multipart 上传 | `b834151` 前后（本轮 Phase 1） | `e2e/user-closure.spec.ts` 上传旅程 |
| 导出字节不确定（zip 时间戳 + docProps） | `7e3038d` | `test_intake_cleaning_export.py` 字节稳定用例 |
| 事实表查询无稳定排序 | `7e3038d` | 同上（跨请求字节一致） |
| StoredObject 假成功引用 | `3700cb6` | `test_succeeded_attempt_persists_reusable_stored_object` |
| 映射确认与源 hash 漂移 | 既有 `mapping_source_mismatch` 门禁 | `tests/api/test_intake.py` |

## 5. 已知未知与未获得证据

1. 顺丰经营现金流净额、所有者权益（yto 同）在 manifest 中为"量级"值，精确值待独立录入；
2. 腾讯 FY2025 年报（留出）全部 key items 待独立录入；
3. D01 `objective_finance_v1.yaml` 的测试与 CI 结果需在 P02 复用时逐项核验（台账称已提交 `c009823`）；
4. GitHub Actions 对 `65345ff` 的实时结论未在本地验证（以 Actions 页面为准）；
5. 独立录入者人选与授权未确认（阻塞 I03 验收，不阻塞非验收性开发）；
6. 2026-09-07 PDF 格式评审轮新登记三项缺陷（JDL 港股同名行项目触发归一化
   唯一键冲突、腾讯种子利润表缺行、引擎"杜邦三分解"与正文杜邦口径差异），
   详见 [格式评审包](2026-09-07-format-review.md) 第 3 节，分别待 P01/P02/P03 处置。
