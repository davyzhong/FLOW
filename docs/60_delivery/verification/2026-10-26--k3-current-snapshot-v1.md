---
doc_id: FLOW-VERIFY-K3-CURRENT-SNAPSHOT-20261026
title: K3 当前 Obsidian 工作区稳定快照复核
doc_type: verification
status: verified
version: 2.7
created_at: 2026-10-26
updated_at: 2026-10-26
owner: FLOW
commit_refs: [davybase-f65df69]
evidence_refs: "[obsidianwiki-k2-2026-10-26-final, stable-working-tree-fingerprint, zero-writer-handles]"
applies_to: knowledge-refresh
---

# K3 当前 Obsidian 工作区稳定快照复核

## 结论

10 月 19 日 accepted manifest 的 Git 状态 SHA 与当前 vault 已漂移，因此不能将旧 K3 source baseline/diff 当作当前内容输入。按 K2 冻结器在 vault 外重新建立当前工作区快照；候选和复验的 HEAD、tree、Git 状态 SHA、完整内容 SHA、文件数、总字节数与 dirty 路径数均相同，写句柄均为 0，结果 accepted。ObsidianWiki 文件未被写入、暂存、提交或清理。

## 快照事实

| 字段 | 结果 |
|---|---|
| Vault | `/Users/qiming/ObsidianWiki`，branch `main` |
| snapshot ID | `obsidianwiki-20261026T003619+0800-4ea1c067` |
| HEAD / tree | `e04d6833a623033a3601d36192f02dc15184eb6e` / `aa7d84d3fff59b0c1dd390fc872beb66cba40f52` |
| Git 状态 SHA-256 | `5f058092c29641f9f4d60b46c07d36437798584e4c4c95864d7a3da629a3f82f` |
| 完整工作区内容 SHA-256 | `c84efd671e2b90e4f69152c3dd04a570d9c378d08fb7a3cb97b86e322f123df0` |
| 纳入文件 / 字节 | 112,010 / 4,260,351,293 |
| dirty 路径 | 1,475 |
| 候选 / 复验 | 完整指纹、数量均一致 |
| 写句柄 | 候选锁定 0；候选 0；复验 0 |
| 状态 | `accepted`；随后完成远端 push 并释放冻结锁 |
| Manifest SHA-256 | `ede08faabcf5c70222fec7c628f9ae778deba82dbdf5bdab26ad154184269e39` |
| Davybase 证据 | [`f65df69` 中的 manifest 与 SHA-256 sidecar](https://github.com/davyzhong/davybase/tree/codex/knowledge-run-manifest-k0/docs/evidence/snapshots) |

旧 accepted manifest SHA 为 `b7e566e68b1119117999fc9ef08f7fae657e6bcbc3d3482d77ea56caf0e44654`，记录 1,377 dirty 路径、111,912 文件和 4,240,118,843 字节。10 月 26 日前置只读扫描观察到 1,434 条 dirty 路径；冻结候选开始时已有 1,475 条。冻结器在候选/复验期间确认完整工作区指纹稳定，故新的 accepted snapshot 是之后 K3 的唯一输入。差异数值代表扫描时点变化，不用于推断具体文档的语义变化。

## 验收方法与下一步

Davybase `scripts/run/freeze_snapshot.py freeze` 运行于分支 `codex/knowledge-run-manifest-k0` 的提交 `f65df69`，将 manifest/sidecar 写入 Davybase 工作区；没有触碰 ObsidianWiki。manifest JSON 可解析，sidecar SHA 与本地 `shasum -a 256` 一致，提交已推送至 GitHub；之后冻结器 `release` 删除其外置锁文件。项目分支工作树干净。

本报告创建时的后续步骤已完成：registry、baseline、delta 与累计 diff 均已按该 snapshot 构建并复验，详见下节。当前已按工作包口径开展只读语义路由和 HIGH 全审；`CURRENT_RELEASE` 继续保持 `flow-knowledge-2026-09-12.1`。


## K3 来源基线与累计差异重建（2026-10-26）

以本报告的 accepted snapshot 和原有 allowlist（`processed/03_财务与会计`、`processed/02_企业管理`、`processed/04_跨境物流`、`processed/微信知识库`、`wiki`）运行 `source_baseline.py build-v2`。生成 9,673 篇来源，ID 唯一；类别为 wiki 6,413、domain-note 1,601、wechat 1,659。与 10-19 baseline 比较的增量为 9,671 篇保持存在、2 篇新增；正文、路径、图片/附录 enrichment 变化均为 0。

累计四维 diff 从 10-19 的 9,956 个 ID 基础应用上述增量，得 9,958 个 ID：新增 6,641、存在 3,032、删除 285；旧的 1,868 个正文变化与 1,310 个 enrichment 变化保持记录。本次新增两条均是 `added`，没有改写历史条目。增量 delta 另行保存，便于复验。基线初建时 9,673 条的 `k_domain` 为 `pending-review`，`authority_level`/`sensitivity` 为 `unclassified`；来源自动登记不冒充语义审阅。后续逐批审阅字段以对应语义台账及基线当前行值为准。

| 文件 | SHA-256 |
|---|---|
| `source-inputs-2026-10-26.yaml` | 已纳入知识库 `sha256sums.txt` |
| `source-id-registry-2026-10-26.tsv` | `ebd33a89055592314a6d24ea9ddce66dcd3caaca2ead33e301324844a17ec83b` |
| `source-baseline-2026-10-26.tsv` | `9905fd9a5c192177f762b7275c86399abe9e63244f6a79d79f07b69b89446277` |
| `source-delta-2026-10-26.tsv` | `689b7761d048e24bf7a879d5d87f4fcd047a527e70b6fdce79ce81a136f49c91` |
| `source-diff-2026-10-26.tsv` | `9e781828298245be3c9b9e295eb5da825d04c6092393913a0fd8d03c36e70b90` |

同一 accepted manifest 重建至独立 `/tmp` 输出目录，registry/baseline/delta 与累计 diff 均逐字节一致。生成后重算的 vault HEAD/tree、状态 SHA、内容 SHA、文件数、字节数与 dirty 路径数全部匹配 accepted manifest，写句柄 0。source baseline 与 coverage validator 专项测试 14/14 通过；知识库清单重生成 2,207 项并 `--check` 通过。全量语义路由、MED/LOW 双审、coverage 闭合、知识综合与独立 reader 尚待完成；语义批次 001–025 已记录 76 条 HIGH 候选（62 篇本地正文已读、14 条仅元数据筛查）；60 条 pending-verification，2 条同源副本 duplicate，14 条内部敏感来源 rejected 并排除候选；第二十批的三篇方法文章仍 pending-verification，示例数字与阈值未获独立证据。`CURRENT_RELEASE` 不变。

## 语义审阅前复验快照（2026-10-26）

基线提交推送后原 manifest 锁已按流程释放，不能在无锁状态重跑 `verify`。随后按 Davybase 冻结器新建 accepted snapshot `obsidianwiki-20261026T005516+0800-d601b4d5`，Davybase 分支 `codex/knowledge-run-manifest-k0` commit `110fe57`。manifest SHA-256 为 `593715c832a538d9ba83df4e077b8dd9bace24f40d3c0d5262fc3779b20f0e77`；候选与复验内容 SHA 均为 `c84efd671e2b90e4f69152c3dd04a570d9c378d08fb7a3cb97b86e322f123df0`，状态 SHA `5f058092c29641f9f4d60b46c07d36437798584e4c4c95864d7a3da629a3f82f`，HEAD/tree、文件数 112,010、总字节数 4,260,351,293、dirty 路径数 1,475 均一致，写句柄 0。它与前一 accepted snapshot 的输入内容完全一致，因此不会改变来源内容；按最新快照 ID 重建后，registry SHA 为 `ebd33a89055592314a6d24ea9ddce66dcd3caaca2ead33e301324844a17ec83b`，baseline SHA 为 `9905fd9a5c192177f762b7275c86399abe9e63244f6a79d79f07b69b89446277`，delta SHA 仍为 `689b7761d048e24bf7a879d5d87f4fcd047a527e70b6fdce79ce81a136f49c91`；独立目录重复构建逐字节一致。另一次尝试因误传 HTTPS canonical remote 被门禁拒绝，拒绝证据同分支保留；使用仓库真实 `origin` 后通过。vault 未写入。


## 语义审阅批次 001（2026-10-26）

从既有 D-wiki HIGH 簇的代表主题中审阅三条来源：三表勾稽（K1）和杜邦分析（K2，related K3）的本地笔记正文已读；现金流分析（K2，related K1）本地文件只有 235 字节元数据，正文缺失，标记 `locator-only`，不得计为全文审阅。三条来源 SHA-256 均与 accepted snapshot baseline 的文件/正文指纹一致；权威级别与敏感级别保持 `unclassified`，处置均 `pending-verification`。逐条证据与理由见 `docs/knowledge-base/10_sources/semantic-review-2026-10-26-batch-001.tsv`。

## 语义审阅批次 002（2026-10-26）

从 A-finance HIGH 簇中审阅三篇本地完整笔记：杜邦分析模型、盈利能力驱动拆解、利润表分析与行业差异。三条 source SHA-256 均与 accepted snapshot baseline 文件及正文指纹一致；主域为 K2，权威级别 unclassified、敏感级别 public，处置 pending-verification。审阅发现杜邦案例文字将 414 亿元写成 41.4 亿元并将资产标为估算值，公式表缺少运算符；利润表行业收入确认说明过度概括。上述数值、公式表达和会计规则均不进入候选事实，待原始出版物与正式准则核验。逐条证据见 `docs/knowledge-base/10_sources/semantic-review-2026-10-26-batch-002.tsv`。


## 语义审阅批次 003（2026-10-26）

审阅 A-finance HIGH 簇 7 的三篇本地完整笔记：三大报表勾稽、现金流量表分析、资产负债表分析。三条 SHA-256 均与 accepted snapshot baseline 的文件及正文指纹一致；分别路由 K1、K2、K2，权威级别保持 unclassified、敏感级别 public、处置 pending-verification。三表勾稽笔记的现金流桥算例不闭合；现金流文章的案例算术可闭合，但阈值与行业判断仍属待核建议；资产负债表文章部分原则过于概括，ROE/EVA 定义不完整。不得把这些问题标记成已证实来源错误；只将其作为本地审阅风险，等待原始出版物与权威口径复核。

## 语义审阅批次 004（2026-10-26）

第四批审阅两篇现金流分析文章与一篇现金流量表编制笔记。三条 SHA-256 匹配 accepted snapshot baseline；分析文章路由 K2，编制笔记路由 K1，均保持 pending-verification。两篇分析材料给出的通用阈值缺少定义、数据依据或适用边界；编制笔记关于报表精度的宽泛说法未经准则支持。上述仅是对本地摘录的审阅结论，原始出版物和正式准则仍待核验。逐条记录见 `semantic-review-2026-10-26-batch-004.tsv`。

## 语义审阅批次 005（2026-10-26）

第五批审阅资产负债表与利润表勾稽、合并报表步骤、资产负债表比率分析三篇本地全文。三条指纹均匹配 accepted snapshot baseline；报表勾稽及合并流程路由 K1，比例分析路由 K2，均为 pending-verification。合并案例中的资产负债/净资产不平衡及权益抵消数无法由所给数字支持；其余内容存在过度简化的会计关系或无出处的通用阈值。不得把疑点直接定性为来源原文事实错误，也不得采纳案例数值/阈值；后续以准则和原始材料核验。详见 `semantic-review-2026-10-26-batch-005.tsv`。

## 语义审阅批次 006（2026-10-26）

第六批审阅合并报表成本法编制、内部交易抵消及合并抵消实践三篇本地全文。哈希均匹配 accepted snapshot baseline；均路由 K1，处置 pending-verification。记录了规范依据不完整、内部利润全额抵销与归属分摊概念混用风险，以及示例省略商誉、购买日差额等前提；不把简化案例作可执行模板。逐条见 `semantic-review-2026-10-26-batch-006.tsv`。

## 语义审阅批次 007（2026-10-26）

第七批审阅一篇三表勾稽文章和两篇财务知识库短摘要，均为本地全文读取；哈希匹配 accepted snapshot，均路由 K1、pending-verification。记录现金流案例未包含完整现金与营运资本信息、短摘要对现金流正负判断缺少业务情境，以及与既有三表资料存在重叠；原始来源关系待核，不能把摘要当完整规格。逐条见 `semantic-review-2026-10-26-batch-007.tsv`。

## 语义审阅批次 008（2026-10-26）

第八批审阅资金预测方法与两篇现金流模型文章，均完成本地全文阅读并匹配 accepted snapshot 哈希，均路由 K6、pending-verification。记录方法论没有实测准确性证据、模型未提供可复算的 workbook 公式及业务覆盖边界；两篇 12 个月模型内容高度重叠，需核对原件以决定是否重复发布，不重复计为独立方法/验证证据。详见 `semantic-review-2026-10-26-batch-008.tsv`。

## 语义审阅批次 009（2026-10-26）

第九批审阅资金缺口模型两篇、财报先行指标文章一篇，均完成全文本地读取，哈希匹配 accepted snapshot，均路由 K6、pending-verification。营运资金周转公式经国家金融监督管理总局 2024 年《流动资金贷款管理办法》附件核对，属于银行测算示例，需结合借款人实际且允许机构调整；文章将银行利率敏感缺口与企业资金缺口并列时必须区分。两篇五模型文章内容高度重叠，待原件核对重复发布。详见 `semantic-review-2026-10-26-batch-009.tsv`。

## 语义审阅批次 010（2026-10-26）

第十批审阅净利润与现金流关系 3 篇，均完成全文本地读取，哈希匹配 accepted snapshot，路由 K2、pending-verification。记录现金流较难伪造的断言过于绝对、咖啡店算例缺期初现金和完整收支且混淆负债余额与现金缺口，以及净利润到经营现金流调节逻辑不能替代完整报表公式。详见 `semantic-review-2026-10-26-batch-010.tsv`。

## 语义审阅批次 011（2026-10-26）

第十一批审阅同账号发布的 1 篇净利润与现金流文章，全文哈希匹配 accepted snapshot，路由 K2、pending-verification。其与 2025-05-24 同题旧文可能存在版本关系，但本地内容不足以确认重复；新增现金流管理阈值未提供来源，转换公式也不完整。详见 `semantic-review-2026-10-26-batch-011.tsv`。

## 语义审阅批次 012（2026-10-26）

第十二批完成内控、收入确认与会计凭证证据链 3 篇全文审阅，哈希匹配 accepted snapshot，均路由 K1、pending-verification。五流框架与凭证清单只能作主题参考，不能视为完整内控方案或通用法定资料要求；收入确认文章引用规则的版本与具体交易适用性仍待核。详见 `semantic-review-2026-10-26-batch-012.tsv`。

## 语义审阅批次 013（2026-10-26）

第十三批审阅自动计费/付款资料 1 篇，全文哈希匹配 accepted snapshot，路由 K7。因含敏感第三方合同及账户信息，标注 project-internal、rejected 并排除产品候选；仅留最小化的风险摘要，不复制具体内容。详见 `semantic-review-2026-10-26-batch-013.tsv`。

## 语义审阅批次 014（2026-10-26）

第十四批审阅 AI 财务应用与业财分析材料 4 篇，全文哈希匹配 accepted snapshot，均 pending-verification。内容含产品推广、假设例子、缺少定义或验证的映射/模型和缺少来源的样例数值，不据此形成产品事实或验收口径。详见 `semantic-review-2026-10-26-batch-014.tsv`。

## 语义审阅批次 015（2026-10-26）

第十五批审阅财务看板和动态指标交互材料 3 篇，全文哈希匹配 accepted snapshot，均 pending-verification。记录财务阈值冲突且缺少行业依据、系列看板匿名示例不可复算，以及 DAX 示例公式与上下文限制。详见 `semantic-review-2026-10-26-batch-015.tsv`。

## 语义审阅批次 016（2026-10-26）

第十六批审阅自动导入财务看板与 PPT 汇报框架 3 篇，全文哈希匹配 accepted snapshot，均 pending-verification。自动看板两篇高度近似但原始版本关系未核，模板与数据未实测；PPT 中示例数字为空位，图表建议缺少可核数据。详见 `semantic-review-2026-10-26-batch-016.tsv`。

## 语义审阅批次 017（2026-10-26）

第十七批审阅三类驾驶舱蓝本全文 3 篇，哈希匹配 accepted snapshot，均 pending-verification。记录离线与自动分析功能未经原型验证、案例数据未独立确认及集团案例中的排序错误；模拟数据仅用于理解图表结构。详见 `semantic-review-2026-10-26-batch-017.tsv`。

## 语义审阅批次 018（2026-10-26）

第十八批复核两条同源管理报表记录。标题与原文 URL 确认相同原始发布物，将副本标记 duplicate；另一条 pending-verification。原始 XLSX 不在快照中，表格公式、自动勾稽和工作表数未实测；AI 图像综合仅作衍生材料。详见 `semantic-review-2026-10-26-batch-018.tsv`。

## 语义审阅批次 019（2026-10-26）

第十九批对 9 条内部业财实践资料进行最小元数据筛查，未打开正文；因来源类型明确指向内部经营/规划信息，标 project-internal/rejected，不进入产品候选。具体企业事实不复制到本报告。详见 `semantic-review-2026-10-26-batch-019.tsv`。


第二十批审阅经营分析闭环、三问法和报告建议三篇全文，源文件 SHA-256 与 accepted baseline 匹配。文章结构可作待验证提问模板；单箱利润变化、铜价/订单示例、>2σ、节省比例、ROI 和建议效果均无附带原始证据，不当作事实、阈值或验收标准。详见 `semantic-review-2026-10-26-batch-020.tsv`。


第二十一批对三张底牌文章全文复核，发现 KPI/阈值及效果缺少来源；与既有微信知识库记录比对原文 URL 后将同发布物副本标 duplicate。半年度总结/计划报告仅看元数据，因可能包含内部经营表现而标 project-internal/rejected，不查看正文。详见 `semantic-review-2026-10-26-batch-021.tsv`。


第二十二批审阅两篇同题“财务分析必须基于业务逻辑”文章及业务穿透分析文章。前两篇内容高度相似，但来源 URL 和发布日期不同，未核明关系，保持独立 pending-verification；案例、阈值与 KPI 均无独立证据。详见 `semantic-review-2026-10-26-batch-022.tsv`。


第二十三批审阅核算粒度、七种经营思维及降本增效汇报三篇全文，案例数字、ROI、阈值及效果没有独立来源；多账套建议不作为普遍要求。详见 `semantic-review-2026-10-26-batch-023.tsv`。


第二十四批对闭环案例链接笔记与 wechat-72e4a10ae09e 正文作比对，发现内容和单箱案例高度相似，但本地无原文 URL 或可追溯原件关联，保留 pending-verification，不标 duplicate；经营驱动树文章中未带底层数据的数字与 BI 看板产品主张保留待核验。详见 `semantic-review-2026-10-26-batch-024.tsv`。


第二十五批只按元数据筛查 3 条余下簇2内部架构/讨论/归集材料，未打开正文，标 project-internal/rejected。覆盖追溯发现旧 A-finance 中 AI 财务专题路径已在 ObsidianWiki 提交 `c743b98972d45794d5948787ab65e7fd9afcbad1` 删除；该提交的 Git tree 显示新系统架构路径与旧财务路径指向同一 blob `2b4dd69c5505711c6b2ea3b4fa5fa4a6d1aebcc3`。新路径不在当前 accepted baseline，因此将旧 HIGH 行登记为基线外迁移并排除当前候选；未读取正文，也未将其计入 76 条已审候选。详见 `semantic-review-2026-10-26-batch-025.tsv` 与本次路径/hash 追溯记录。

第二十六至三十一批对旧 W1 MED 17 篇组完成 17 篇双审。coverage 表覆盖 9,673 个当前 baseline source_id，其中 routed 87、filtered 16、pending_review 9,570；严格终态尚未闭合。第30批三篇分别标记为 K2/K1/K4 主域及相关域，均为 pending-verification；财务比率概念/阈值、三表关系简化和无来源投资案例不作产品事实。详见 `semantic-review-2026-10-26-batch-030.tsv`。京东季度拆分项合计高出合并净收入 181.5 亿元；数据驱动看板优先级计数 28,155 高于总量 26,935，占比合计约 104.6%。均未核原始来源前排除产品事实使用。


## 语义审阅批次 030（2026-10-26）

第五组旧 W1 MED 材料完成 3 篇双审，均与 accepted baseline 正文 SHA 匹配，保留 pending-verification。财务指标入门材料存在总资产周转率概念混淆、流动比率阈值泛化及 EBITDA 横向比较边界问题；三表入门将现金流简化为利润表实收版，不能单凭经营现金流长期为正断言持续造血；管理者财务思维中的降价销量翻倍依赖单位成本不变等前提，餐饮 IRR 7% 和 30 个月回本无可追溯原始数据。均不作为产品定义、投资证据或行业阈值。coverage 更新为 routed 75、filtered 16、pending_review 9,582。逐条证据见 `semantic-review-2026-10-26-batch-030.tsv`。


## 语义审阅批次 031（2026-10-26）

本批完成旧 W1 MED 17 篇组最后三条来源双审，均匹配 accepted baseline 的正文 SHA，保留 pending-verification。组织绩效模板的目标完成过滤期间与结论期间不一致、正文指标基线与图中警戒线冲突，且权重/评分公式缺少完整口径；营销绩效材料中的 K 值解释、指标利润率以及 40/30/30 权重与复用仪表板口径不一，数据和案例结论缺原始资料；匿名共享中心绩效案例未提供原始样本、数据和统计检验，分钟折算、正态分布与性别/组别因果归因不能独立核实，绩效排名与减编主张不能泛化为制度建议。coverage 更新为 routed 87、filtered 16、pending_review 9,570。详见 `semantic-review-2026-10-26-batch-031.tsv`。


## 语义审阅批次 032（2026-10-26）

从 W3 MED 分层首批抽审三条正文，文件 SHA 与 accepted baseline 一致，均为 pending-verification。回归文章将相关性/拟合度及显著性检验简化为普适判断，示例样本不完整；波特五力的市场进入时点陈述与投票图缺乏可核证据；门店品类调整报告以相邻期间比较推断策略效果，缺少对照/混杂因素控制，正文和图示中的时间、转化与期间指标存在口径差异。coverage 为 routed 87、filtered 16、pending_review 9,570。详见 `semantic-review-2026-10-26-batch-032.tsv`。


## 语义审阅批次 033（2026-10-26）

W3 MED 第二组抽审三条来源，文件 SHA 与 accepted baseline 一致，处置均 pending-verification。电商驾驶舱列出多类成交/流量/推广指标，但未见统计定义、原始数据和模板复现；零售框架仅提供建议，没有独立验证效率或预测效果；2024-08-08 与 2024-08-22 两篇文章正文高度相似，但原文 URL 和日期不同，未核清来源关系前不合并。正文与生成附录分开取证，不采纳未核附录中的指标数字。coverage 更新为 routed 87、filtered 16、pending_review 9,570。详见 `semantic-review-2026-10-26-batch-033.tsv`。


## 语义审阅批次 034（2026-10-26）

W3 MED 第三组抽审三条全文，source SHA 均与 accepted baseline 匹配，处置为 pending-verification。人货匹配模板可参考其问题分解，历史销售不足以独立预测新品需求；BI科普中的边界定义与FineBI实时预警、预算审批等能力未独立验证；零售多场景案例涉及星型模型、购物篮和RFM，但无原始数据/工作簿，AI派生图表数据存在跨图差异，不作事实。coverage 当前 routed 87、filtered 16、pending_review 9,570。详见 `semantic-review-2026-10-26-batch-034.tsv`。


## 语义审阅批次 035（2026-10-26）

W3 MED 第四组完成三条全文双审，三条源 SHA 均匹配 accepted baseline，处置均为 pending-verification。零售B2B案例将地区和排名数据映射改写、按随机函数产生目标，所有案例数值/趋势不作经营事实；业财一体化材料无企业实施证据且包含工具推广；零售五场景文章缺数据、口径与模型，固定ABC占比和效果主张不作通用规则。coverage 更新为 routed 90、filtered 16、pending_review 9,567。详见 `semantic-review-2026-10-26-batch-035.tsv`。


## 语义审阅批次 036（2026-10-26）

W3 MED 第五组完成三条全文双审，源 SHA 与 accepted baseline 一致，均为 pending-verification。电商指标文章存在库存周转公式/量纲与分母口径切换；新品推广的脱敏样本、虚拟品牌与客户分群无底表可复算，Q1完成率不足以证明Q2目标合理；房地产案例虽描述企业及外部数据来源，但未附复核数据/时间与清洗规则，观察性对比不能证明因果或作为投资结论。coverage 更新至 routed 93、filtered 16、pending_review 9,564。详见 `semantic-review-2026-10-26-batch-036.tsv`。


## 语义审阅批次 037（2026-10-26）

W3 MED 第六组完成三条全文双审，三条源 SHA 与 accepted baseline 一致，处置均为 pending-verification。年度报告案例只有2010–2018九行年度汇总，不能支持客户/商品级结论或因果；门店鞋类折扣与目标完成率的比较缺混杂控制，无法验证折扣导致未达标；供应链文章的匿名案例、SCOR版本、APQC对标及供应商产品能力未提供原始材料和可复算效果。coverage 更新为 routed 96、filtered 16、pending_review 9,561。详见 `semantic-review-2026-10-26-batch-037.tsv`。


## 语义审阅批次 038（2026-10-26）

W3 MED 第七组完成三条全文双审，源 SHA 均匹配 accepted baseline，处置均为 pending-verification。竞品分析图表数据明示并非企业实绩；FineBI财务数字化和费用案例为供应商自述、无原始指标或独立效果验证；库存ABC/XYZ阈值及批次逆推库龄依赖业务约定与完整流水，不能直接当普适规则或真实库龄。coverage 更新至 routed 99、filtered 16、pending_review 9,558。详见 `semantic-review-2026-10-26-batch-038.tsv`。


## 语义审阅批次 039（2026-10-26）

W3 MED 第八组完成三条全文双审，正文 SHA 匹配 accepted baseline 且不与既有语义批次重复，均为 pending-verification。财务BP示例来自称为脱敏的订单/支付宝数据，正文列值还存在 19,947.05−556.75−3,283.09=16,107.21 元而列报 16,312.06 元的204.85元内部差异，妥投率等衍生值须重算，经营口径不替代会计定义；渠道重点商品专案缺少可复算明细与对照，观察到的份额/达成不能证明措施效果；客户分析模型文章缺少样本、标签、验证和性能证据，标题数量/分节对应不清，正相关不是干预因果。coverage 为 routed 102、filtered 16、pending_review 9,555。详见 `semantic-review-2026-10-26-batch-039.tsv`。


## 语义审阅批次 040（2026-10-26）

W3 MED 第九组完成三条全文双审，正文 SHA 匹配 accepted baseline 且此前未审，均为 pending-verification。供应链直播整理中的成熟度模型版本、指标目标和15%/2%效果缺权威依据；财务BI文章带产品推广，后附AI生成模型情景缺原始数据、口径和独立验证；电商店铺数据表未随来源提供，AI附录把退款订单率约54.49%和退款金额率约48.82%均称退款率，已分别标注，禁止混用。coverage 为 routed 105、filtered 16、pending_review 9,552。详见 `semantic-review-2026-10-26-batch-040.tsv`。


## 语义审阅批次 041（2026-10-26）

W3 MED 第十组完成三条全文双审，正文 SHA 匹配 accepted baseline 且此前未审，均为 pending-verification。金融机构指标及“监管合规/实时”看板主张无权威定义和独立验证；电商销售渠道案例原始底表未附，AI生成附录2017销售额同比计算与其列出的年度数不符（24,491,328相对27,902,378约为-12.22%（精确值-12.22494%），非-19.21%）；女装RFM、购物篮阈值与策略不可脱离案例样本泛化。coverage 为 routed 108、filtered 16、pending_review 9,549。详见 `semantic-review-2026-10-26-batch-041.tsv`。


## 语义审阅批次 042（2026-10-26）

W3 MED 第十一组完成三条全文双审，正文 SHA 匹配 accepted baseline 且此前未审，均为 pending-verification。业财BI厂商宣称报表时间缩短80%、培训200人等缺可核基线，BI分析不等同总账核算/自动合规；Excel/BI“效率分”无定义及基准；电商对账示例未给完整结账差异闭环，建模须验证明细粒度、唯一键、维度版本及退款/拆单造成的重复风险，对账证据与审批不能由看板替代。coverage 为 routed 111、filtered 16、pending_review 9,546。详见 `semantic-review-2026-10-26-batch-042.tsv`。


## 语义审阅批次 043（2026-10-26）

W3 MED 第十二组完成三条全文双审，正文 SHA 匹配 accepted baseline 且此前未审，均为 pending-verification。校服案例全年度结果、利润和RFM策略无底表/阈值，生成附录所示可见时间范围与全年结论需回查；万昌财务BP为BI厂商直播案例且无基线成效；竞品分析第三方市场数据和雷达评分缺原始方法，广告投入导致留存低的解释无对照证据。coverage 为 routed 114、filtered 16、pending_review 9,543。详见 `semantic-review-2026-10-26-batch-043.tsv`。


## 语义审阅批次 044（2026-10-26）

W3 MED 第十三组完成三条全文双审，正文 SHA 匹配 accepted baseline 且此前未审，均为 pending-verification。盈亏平衡公式转录缺运算符，数值暗示除法但需核原图；Altman Z-Score变量描述与1968经典模型不同且未注明版本；DeepSeek效率对比为个人叙述，“90%岗位”是反问假设，没有量化性能或劳动力证据。coverage 为 routed 117、filtered 16、pending_review 9,540。详见 `semantic-review-2026-10-26-batch-044.tsv`。


## 语义审阅批次 045（2026-10-26）

W3 MED 第十四组完成三条全文双审，正文 SHA 匹配 accepted baseline 且此前未审，均为 pending-verification。电商报告无可复算底表；AI因果发现、准确率提升及五分钟效率主张无基线；风险文章的市场规模、退货率、库存和流失数字缺来源/分母/范围，预警工具能力与阈值未独立验证。coverage 为 routed 120、filtered 16、pending_review 9,537。详见 `semantic-review-2026-10-26-batch-045.tsv`。


## 语义审阅批次 046（2026-10-26）

W3 MED 第十五组完成三条全文双审，均为 pending-verification。财务四看板缺比较底表、期间和行业样本；渠道示例ROI未扣商品/平台成本且无增量归因；电商成本行业统计缺成本分母/总体范围，案例数据不可复核。coverage 为 routed 123、filtered 16、pending_review 9,534。详见 `semantic-review-2026-10-26-batch-046.tsv`。


## 语义审阅批次 047（2026-10-26）

W3 MED 第十六组完成三条全文双审，均保留 pending-verification。人效案例的绩效/晋升/薪酬图表无可追溯依据且涉及人事数据；转型失败70%断言未给研究；电商盈利引用中报告名称与TOP100数据期间关系不明，退货率敏感度缺方法。coverage 为 routed 126、filtered 16、pending_review 9,531。详见 `semantic-review-2026-10-26-batch-047.tsv`。


## 语义审阅批次 048（2026-10-26）

W3 MED 第十七组完成三条全文双审，均保留 pending-verification。财务文章所述马斯克审计团队效率、五角大楼预算黑洞及95%岗位替代未给可核来源，AI附录置信度标注不是证据；分析方法案例附录不可复算，关联不能推作因果；LTV/CAC≥3未定义收益口径与回收期，非普适阈值。coverage 为 routed 129、filtered 16、pending_review 9,528。详见 `semantic-review-2026-10-26-batch-048.tsv`。


## 语义审阅批次 049（2026-10-26）

W3 MED 第十八组完成三条全文双审，均保留 pending-verification。BI市场规模及前三档渗透率缺来源与分类定义，附录虽将智能BI 100%标作理论目标但未给定义或依据；六步流程图仅作概览而不替代数据治理控制；36模型清单不代表完整或有效。coverage 为 routed 132、filtered 16、pending_review 9,525。详见 `semantic-review-2026-10-26-batch-049.tsv`。


## 语义审阅批次 050（2026-10-26）

W3 MED 第十九组完成三条全文双审，均为 pending-verification。母婴看板缺原始交易表及份额/同比口径；波士顿矩阵宝洁案例缺期间、市场分母与原始数据，象限策略是启发式。2022/2023同题文章在核心内容上重合，保留两条来源、不合并。coverage 为 routed 135、filtered 16、pending_review 9,522。详见 `semantic-review-2026-10-26-batch-050.tsv`。


## 语义审阅批次 051（2026-10-26）

W3 MED 第二十组完成三条全文双审，均保留 pending-verification。模型合集“8种”标题与“15种”摘要不一致；RFM分位阈值依赖样本、M口径可变；折扣购买筛选不能证明“羊毛党”身份，案例人数和策略收益缺复核。coverage 为 routed 138、filtered 16、pending_review 9,519。详见 `semantic-review-2026-10-26-batch-051.tsv`。
