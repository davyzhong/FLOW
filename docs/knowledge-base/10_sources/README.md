---
doc_id: FLOW-SRC-README-001
title: 来源与证据层
doc_type: navigation
status: current
version: 2.7
created_at: 2026-09-12
updated_at: 2026-10-26
owner: FLOW
applies_to: knowledge-base
---

# 来源与证据层（10_sources）

回答「这条知识从哪里来、是否允许使用」，不承担产品结论。

- `SOURCE_REGISTER.md` —— 来源登记册（人类可读）与分层登记策略
- `source-register.tsv` —— 机器可读登记（活登记，知识卡按需追加篇级）
- `snapshots/` —— 固定截面定义（当前唯一截面：obsidian-2026-09-12T15:46+08:00）
- `coverage-2026-10-26.tsv`、`coverage-exceptions-2026-10-26.tsv` 与 `../00_governance/change-manifests/obsidianwiki-20261026T005516+0800-d601b4d5-l2.tsv` —— 9,673 个来源的逐 ID 进度、例外与变更追溯；当前 routed 117、filtered 16、pending_review 9,540。
- `source-baseline-2026-10-26.tsv`、`source-delta-2026-10-26.tsv`、
  `source-diff-2026-10-26.tsv` 与 `../00_governance/migration/source-id-registry-2026-10-26.tsv`
  —— K3 当前资料内容来自 `obsidianwiki-20261026T005516+0800-d601b4d5`。当前 registry/baseline/delta 已统一绑定该 accepted snapshot；已审阅条目的语义字段按批次登记，其余来源仍待审，不能视为已路由或可采纳。详见[当前快照与基线复核](../../60_delivery/verification/2026-10-26--k3-current-snapshot-v1.md)。
- 同名 `2026-10-19` 文件仅代表旧 accepted 工作区截面，保留为历史证据，不再作为当前输入。旧历史没有完整改名 registry，因此未确认的改名以新增/删除分别登记，不以标题相似度推断。
- `semantic-review-2026-10-26-batch-001.tsv` —— 首批 3 条 HIGH 主题候选的只读路由/可读性记录；不代表来源采纳或原始来源核验完成。
- `semantic-review-2026-10-26-batch-002.tsv` —— 第二批 3 条 HIGH 候选的全笔记核验、路由和内容风险记录；原始来源核验及采纳仍未完成。
- `source_notes/`（M2 后启用）—— 外部研究摘要（自 02_research/synthesis 迁入，M2 后续批次）

处置枚举：adopted / partially-adopted / duplicate / background / rejected / pending-verification；核验等级独立记录（program-routed / representative-read / human-verified）。
- `semantic-review-2026-10-26-batch-004.tsv` —— 第四批 3 条 HIGH 候选的全文审阅与现金流阈值/编制口径风险记录；均为 pending-verification。
- `semantic-review-2026-10-26-batch-005.tsv` —— 第五批 3 条 HIGH 候选全文审阅，记录合并报表案例不平衡、勾稽简化及通用指标阈值风险；均 pending-verification。
- `semantic-review-2026-10-26-batch-006.tsv` —— 第六批 3 条 HIGH 候选全文审阅，记录合并会计处理和内部交易抵消的规则边界风险；均 pending-verification。
- `semantic-review-2026-10-26-batch-007.tsv` —— 第七批 3 条 HIGH 候选全文审阅，记录三表案例信息不全、现金流编制摘要缺少边界及同主题材料重叠；均 pending-verification。
- `semantic-review-2026-10-26-batch-008.tsv` —— 第八批 3 条 HIGH/K6 全文审阅，覆盖资金预测方法与现金流模型；记录模型简化和两篇疑似重复发布，均 pending-verification。
- `semantic-review-2026-10-26-batch-009.tsv` —— 第九批 3 条 HIGH/K6 全文审阅，包含 2024 年流动资金贷款规则的官方来源核对、模型边界及重复候选记录；均 pending-verification。
- `semantic-review-2026-10-26-batch-010.tsv` —— 第十批 3 条 HIGH/K2 全文审阅，记录净利润与现金流关系的算例缺项、公式边界及防舞弊表述风险；均 pending-verification。
- `semantic-review-2026-10-26-batch-011.tsv` —— 第十一批 1 条 HIGH/K2 全文审阅，记录同主题可能更新版、现金流管理阈值缺少依据及公式简化；pending-verification。
- `semantic-review-2026-10-26-batch-012.tsv` —— 第十二批 3 条 HIGH/K1 全文审阅，覆盖内控五流、收入确认与记账凭证证据链；记录规则概括及清单边界问题，均 pending-verification。
- `semantic-review-2026-10-26-batch-013.tsv` —— 第十三批 1 条 HIGH/K7 全文审阅；来源含敏感合同/付款资料，已标 project-internal 并排除候选，不在本库复述明细。
- `semantic-review-2026-10-26-batch-014.tsv` —— 第十四批 4 条 HIGH 全文审阅，覆盖 AI 财务、业财模型与分析框架；促销内容、无来源数字、缺公式/验证等均留待核验。
- `semantic-review-2026-10-26-batch-015.tsv` —— 第十五批 3 条 HIGH/K5 全文审阅，覆盖财务能力看板与动态指标切换；阈值冲突、匿名案例和简化公式留待核验。
- `semantic-review-2026-10-26-batch-016.tsv` —— 第十六批 3 条 HIGH/K4/K5 全文审阅，覆盖自动导入看板（含疑似重发）与财务分析 PPT 框架；均缺实物/原始数据验证。
- `semantic-review-2026-10-26-batch-017.tsv` —— 第十七批 3 条 HIGH/K5 驾驶舱蓝本全文审阅；记录演示数据来源、数值排序与未验证产品自述限制。
- `semantic-review-2026-10-26-batch-018.tsv` —— 第十八批 2 条 HIGH/K5 同源管理报表记录；一条待验证，一条同源副本标记 duplicate，未取得原始 XLSX。
- `semantic-review-2026-10-26-batch-019.tsv` —— 第十九批对 9 条 HIGH/簇2 内部资料做元数据筛查；标为 project-internal 并排除产品候选，未展开内容审阅。

- `semantic-review-2026-10-26-batch-020.tsv` —— 第二十批 3 条 HIGH/簇3 经营分析方法全文审阅；示例数据、阈值和效果缺少独立依据，均待核验。

- `semantic-review-2026-10-26-batch-021.tsv` —— 第二十一批 3 条 HIGH/簇3 记录：KPI/阈值证据缺失、同发布物副本去重，以及可能含内部经营数据的报告元数据筛查。

- `semantic-review-2026-10-26-batch-022.tsv` —— 第二十二批 3 条 HIGH/簇3 全文审阅，记录案例证据缺失、不同日期/URL 的同题文章暂不合并，以及业务映射文章的示例阈值不采纳。

- `semantic-review-2026-10-26-batch-023.tsv` —— 第二十三批 3 条 HIGH/簇3 全文审阅；核算粒度、经营思维、汇报框架中的案例数字、ROI 和操作阈值均缺少独立证据，保留为待核验。

- `semantic-review-2026-10-26-batch-024.tsv` —— 第二十四批 2 条 HIGH/簇3 审阅：闭环案例 Getnote 笔记与既有文章高度相似但原文关联未核，暂不标 duplicate；经营驱动树文章保留待验证，未采纳无来源数字与 BI 能力主张。

- `semantic-review-2026-10-26-batch-025.tsv` —— 第二十五批 3 条 HIGH/簇2 内部业财架构与规则资料，均只作元数据筛查并标 project-internal/rejected。
- `semantic-review-2026-10-26-batch-026.tsv` —— 第二十六批旧 W1 MED 组首 3 条双审；原始事实未逐项核对，京东分部收入差额列为不可用于产品事实的风险。
- `semantic-review-2026-10-26-batch-027.tsv` —— 第二十七批旧 W1 MED 组第 2 组 3 条双审；泡泡玛特时点数据无来源、制度/流程二分过度概括、工单看板计数及占比不一致。
- `semantic-review-2026-10-26-batch-028.tsv` —— 第二十八批旧 W1 MED 组第 3 组 3 条双审；Power BI/AI宣传能力及产品时价未核，AI就业预测无证据。
- `semantic-review-2026-10-26-batch-029.tsv` —— 第二十九批旧 W1 MED 组第 4 组 3 条双审；盈利指标公式有量纲/口径风险，酒店指标定义与效果案例无可追溯证据。
- `semantic-review-2026-10-26-batch-030.tsv` —— 第三十批旧 W1 MED 组第 5 组 3 条双审；记录财务比率概念与阈值风险、三表关系简化及无来源投资案例。
- `semantic-review-2026-10-26-batch-031.tsv` —— 第三十一批完成旧 W1 MED 17 篇队列的最后 3 条来源双审；记录绩效口径冲突及匿名案例数据/因果结论的证据限制。
- `semantic-review-2026-10-26-batch-032.tsv` —— 第三十二批从 W3 MED 分层抽审3条，记录回归统计简化、时点性五力案例未经证实、门店策略效果无对照及数据口径矛盾。
- `semantic-review-2026-10-26-batch-033.tsv` —— 第三十三批续审 W3 MED 3条，记录电商驾驶舱指标定义/数据验证缺口及零售系列文的高度相似、原稿关系待核。
- `semantic-review-2026-10-26-batch-034.tsv` —— 第三十四批续审 W3 MED 3条，记录人货匹配预测边界、BI产品能力推广主张未核及零售RFM/购物篮案例缺原始数据。
- 旧 A-finance HIGH 清单中的 AI 财务专题经 ObsidianWiki Git 提交 `c743b98972d45794d5948787ab65e7fd9afcbad1` 证实为跨目录同 blob 迁移；迁入路径不在当前 accepted baseline，故作为基线外迁移从本轮候选排除，不计入 76 条已审候选，正文未打开。详见当前快照复核报告。
- `semantic-review-2026-10-26-batch-035.tsv` —— 第三十五批续审 W3 MED 3条，记录合成销售目标/区域映射、业财一体化宣传主张和零售分析场景的验证边界。
- `semantic-review-2026-10-26-batch-036.tsv` —— 第三十六批续审 W3 MED 3条，记录电商周转/转化指标口径问题、新品拓客分群的样本与假设限制，以及房地产观察性案例的因果和数据来源缺口。
- `semantic-review-2026-10-26-batch-037.tsv` —— 第三十七批续审 W3 MED 3条，记录小样本年度汇总的推断边界、门店折扣归因缺乏控制，以及供应链指标/厂商案例需要原始标准与数据核实。
- `semantic-review-2026-10-26-batch-038.tsv` —— 第三十八批续审 W3 MED 3条，记录非真实竞品看板数值、供应商财务BI自述及库存分类/库龄推算的适用条件。
- `semantic-review-2026-10-26-batch-039.tsv` —— 第三十九批续审 W3 MED 3条，记录财务BP脱敏样本、公式金额矛盾与经营口径、渠道专案的归因限制，以及模型清单的定义/验证边界。
- `semantic-review-2026-10-26-batch-040.tsv` —— 第四十批续审 W3 MED 3条，记录供应链成熟度/ROI示例未经核验、财务BI厂商及AI附录证据边界、电商退款订单率与金额率混淆。
- `semantic-review-2026-10-26-batch-041.tsv` —— 第四十一批续审 W3 MED 3条，记录金融监管/会计指标边界、电商渠道年份增速算术错误及女装RFM/购物篮阈值条件。
- `semantic-review-2026-10-26-batch-042.tsv` —— 第四十二批续审 W3 MED 3条，记录BI厂商案例效果不可核、Excel/BI评分缺基准、对账模型需验证粒度/键/结账闭环。
- `semantic-review-2026-10-26-batch-043.tsv` —— 第四十三批续审 W3 MED 3条，记录校服案例年度数据覆盖待核、财务BP厂商案例无量化验证、竞品第三方数据/因果归因不足。
- `semantic-review-2026-10-26-batch-044.tsv` —— 第四十四批续审 W3 MED 3条，登记盈亏平衡公式转录歧义、Altman经典模型变量不一致、AI性能/就业主张缺量化证据。
