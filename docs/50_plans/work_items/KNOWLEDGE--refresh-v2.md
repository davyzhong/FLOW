---
doc_id: FLOW-WI-KNOWLEDGE-REFRESH-V2-001
title: 第二代静态知识刷新与战略重基线
doc_type: work-item
status: active
version: 5.9
created_at: 2026-09-24
updated_at: 2026-10-26
owner: FLOW
depends_on: [FLOW-DESIGN-KNOWLEDGE-REFRESH-002]
acceptance_refs: [FLOW-PLAN-INTEGRATED-EXECUTION-20260924, FLOW-DESIGN-KNOWLEDGE-REFRESH-002]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: knowledge-system
---

# 第二代静态知识刷新与战略重基线

## 范围

验收 Davybase 图片批次，补齐非微信核心目录图片覆盖，取得随时可启动、内容可复验的
Obsidian 工作区快照，重建 FLOW 来源基线与 sealed knowledge candidate；用户完成
战略裁决后，才原子激活新 release、产品文档和路线图。

## 当前断点

- 批准规格和三仓库 preflight 已完成。
- K0/K1/K2 已完成，K3 当前实际执行。FLOW 的实际资料源是 ObsidianWiki；Davybase 仅承载过快照工具与一次性证据，不构成 FLOW 代码、运行时或产品依赖。当前 accepted working-tree manifest 为 `obsidianwiki-20261026T005516+0800-d601b4d5`（SHA-256 `593715c832a538d9ba83df4e077b8dd9bace24f40d3c0d5262fc3779b20f0e77`）：ObsidianWiki `main@e04d6833`、1,475 条 dirty 路径、112,010 个文件/4,260,351,293 字节；候选/复验全部指纹一致，可写句柄 0，完整内容 SHA `c84efd671e2b90e4f69152c3dd04a570d9c378d08fb7a3cb97b86e322f123df0`。它与此前基线输入 snapshot 内容指纹完全相同；registry/baseline/delta 已按最新 snapshot ID 重建并逐字节复验。ObsidianWiki 不写入；K4–K6 与战略裁决仍未完成。详见[当前快照与基线复核](../../60_delivery/verification/2026-10-26--k3-current-snapshot-v1.md)及 Davybase 分支 `codex/knowledge-run-manifest-k0` 的快照证据。
- 2026-10-17 只读 preflight：Davybase `main`=`6efcd6e2f0560e019f69dbbeada70e2532544f31`；审计实现在 `codex/knowledge-run-manifest-k0`，提交 `172a099`，K0 证据 `94fc05d`，交接/统计 `eb8c3d0` 均已推送。ObsidianWiki `main`=`e04d6833a623033a3601d36192f02dc15184eb6e`，K0 记录 1,365 条本地变化及内容哈希；全范围文件树摘要 `0a42346d276917c8b94f1b0c198ca5bfd68405c35c1656407bc10135e236c7f7` 复验一致。既存变化只读保护，不暂存、不提交、不覆盖，不能把 HEAD 单独称为完整工作区快照。
- `CURRENT_RELEASE` 继续为 `flow-knowledge-2026-09-12.1`。

## K0 完成：审计 envelope 与旧批次回顾性验收（2026-10-17）

实现 `davybase-knowledge-run/v1`、正文/图片 SHA-256 和互斥终态；apply 必须指定 run ID/manifest，dirty 代码或输入仓库 fail closed，dry-run 不写清单。历史 Git 输出快照实测 1,265 输入、1,241 篇 `done=true`；其中 2 篇各记 1 张失败图，严格终态为 1,239 成功、2 待复核、24 过滤。机器清单 strict PASS，32 篇确定性分层样本和 512 张图片逐项对账通过；清单 SHA-256 `c603baab83f7873c852681c69dfb314e7004e43b230ea832fb2a1e9043ce26bc`。872 项 pytest、Ruff、README 统计和链接检查通过；该实现 SHA 的 GitHub `ci.yml` 未运行。历史批次缺 prompt SHA-256，全部 1,265 篇 nonconformant，不计完整 L1 coverage。FLOW 仅保留汇总、定位符与哈希，不复制全文或图片。详见 Davybase 分支 `codex/knowledge-run-manifest-k0` 的验收证据。

ObsidianWiki 的 dirty working tree 不得被清理、重置或用 pull 覆盖；K0 不运行任何 `--apply`。pre-K1 快照同时记录 HEAD/tree、1,365 条 dirty 路径、其内容哈希及整个微信知识库范围文件树摘要，不能伪称仅有 Git HEAD 能代表全部 vault 内容。

## K1 完成：非微信图片覆盖只读盘点（2026-10-17）

Davybase 分支 `codex/knowledge-run-manifest-k0` 推送扫描器实现 `a0c2e6762c2c212baa23f4ea4855dde5399c37a6`，
扫描证据提交 `a914830`。报告绑定实现 SHA，覆盖范围为
`processed/02_企业管理`、`processed/03_财务与会计`、`processed/04_跨境物流`。

扫描结果：1,601 篇 Markdown，1,004 篇含图片语法，438 篇已有受保护图解，566 篇待人工排查；
17,450 个 Obsidian embed 引用在当前 allowlist/resolver 下未解析，另有 2,445 个标准 Markdown
图片引用不受现有处理器支持。可执行候选 0，triage pathspec 566，范围外引用、解析错误、符号链接越界和处理失败均为 0。未解析仅表示本扫描范围与 resolver 未找到，不证明其他目录不存在原图。

证据文件：Davybase `docs/evidence/runs/K1-20261017-nonwechat-image-coverage.json`
（SHA-256 `19f94d39dfda5d19af93e1c1c9cf9ceb608387ee76a40da135f1633dded856db`）、空候选 pathspec
（SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`）、triage pathspec
（SHA-256 `dc43a968c5adf30ab41bf889b2542f385093ff8c7e1e5d10d994e7c6e9e3fafe`）。针对 scanner 的独立审查未发现未解决的 P1/P2。

本步未写入 ObsidianWiki；K0 记录的 1,365 条 dirty 路径内容指纹
`f3bf5fc0edb8981fa0a93b16915d26197963df3d56c9e13cdfdae0dd6d5ab5cf` 复验一致。
工作区仍 dirty，`davybase-knowledge-run/v1` 的 clean-input 前置条件仍不满足；禁止绕过门禁。

## K2 完成：即时稳定工作区快照（2026-10-19）

K2 accepted working-tree manifest 已提交并推送至 Davybase，远端确认后释放锁。快照对 tracked 和未忽略 untracked 文件建 SHA-256 内容指纹，不强制固定时段或 clean；两次 HEAD、tree、Git 状态、内容指纹、文件数与字节数完全一致，且未发现 vault 内可写句柄。快照覆盖 111,912 个文件、4,240,118,843 字节，清单 SHA-256 `b7e566e68b1119117999fc9ef08f7fae657e6bcbc3d3482d77ea56caf0e44654`。Davybase `make check` 897 项通过、专项 18 项通过、文档断链 0；该分支未触发 CI。验收报告：[K2 working-tree snapshot](../../60_delivery/verification/2026-10-19--k2-working-tree-snapshot-v1.md)。

## 当前队首：K3 来源基线、全量差异与知识候选

2026-10-19 accepted manifest `obsidianwiki-20261019T075638+0800-0c0ac842`（SHA-256 `b7e566e68b1119117999fc9ef08f7fae657e6bcbc3d3482d77ea56caf0e44654`）为历史输入。10-26 重取了稳定快照；`obsidianwiki-20261026T003619+0800-4ea1c067` 与后续语义审阅快照 `obsidianwiki-20261026T005516+0800-d601b4d5` 的内容、Git 状态、HEAD/tree、文件数量和 dirty 路径数完全相同。registry/baseline/delta 已绑定后者（manifest SHA-256 `593715c832a538d9ba83df4e077b8dd9bace24f40d3c0d5262fc3779b20f0e77`），重复构建逐字节一致。

10-19 K3 自动来源基线与四维差异已完成，结果（allowlist 9,671 篇，universe 9,956 条）仅适用于 10-19 accepted snapshot，见[历史来源基线验收](../../60_delivery/verification/2026-10-19--k3-source-baseline-v2.md)。10-26 registry/baseline/diff 已重建并在生成后复验 vault 指纹：来源 9,673、唯一 ID 9,673；相较 10-19 baseline 增量为 2 篇新增，0 篇既有正文/路径/enrichment 变化。累计 diff 为 9,958 ID（新增 6,641、存在 3,032、删除 285）。独立目录重复生成逐字节一致；详情见[当前快照与基线复核](../../60_delivery/verification/2026-10-26--k3-current-snapshot-v1.md)。当前下一步转为全量语义路由与 HIGH/MED/LOW 审阅。实现包含 `build-v2` 和严格 coverage 闭合校验器。

**当前子步仍属 K3，未完成整轨验收**：旧 2026-09-12 HIGH 清单的 76 条审阅已完成；当前 9,673 来源的全量逐条路由、MED/LOW 双审、错误集中度检查、coverage 终态闭合、知识综合和独立 reader 尚待完成。coverage 当前 routed 93、filtered 16、pending_review 9,564。旧 2026-09-12 baseline 没有完整历史改名 registry；本轮以精确路径迁移旧 ID，未匹配项记为新增/删除，不用标题相似度推断改名。不得据此声称“没有改名”。`CURRENT_RELEASE` 仍为 `flow-knowledge-2026-09-12.1`，未 seal、未激活。

语义批次 001–025 共记录 76 条 HIGH 候选：62 篇本地笔记正文已读、14 条仅元数据筛查；60 条为 `pending-verification`，2 条同源副本 `duplicate`，14 条内部敏感来源 `rejected` 并排除产品候选，不进入 candidate。批次 001 见[`batch-001`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-001.tsv)，批次 002 见[`batch-002`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-002.tsv)，批次 003 见[`batch-003`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-003.tsv)，批次 004 见[`batch-004`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-004.tsv)，批次 005 见[`batch-005`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-005.tsv)，批次 006 见[`batch-006`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-006.tsv)，批次 007 见[`batch-007`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-007.tsv)，批次 008 见[`batch-008`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-008.tsv)，批次 009 见[`batch-009`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-009.tsv)，[`batch-010`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-010.tsv)，[`batch-011`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-011.tsv)，[`batch-012`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-012.tsv)，[`batch-013`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-013.tsv)，[`batch-014`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-014.tsv)，[`batch-015`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-015.tsv)，[`batch-016`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-016.tsv)，[`batch-017`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-017.tsv)，[`batch-018`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-018.tsv)，[`batch-019`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-019.tsv), [`batch-020`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-020.tsv), [`batch-021`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-021.tsv), [`batch-022`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-022.tsv), [`batch-023`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-023.tsv), [`batch-024`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-024.tsv), [`batch-025`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-025.tsv)。来源原文未独立核验；已记录单位冲突、公式符号缺失、算例不闭合、阈值缺乏依据及定义过度概括等风险，详见审阅台账。

### K3 语义审阅操作口径（依既有规格执行）

- 主域只允许 K1–K8，定义以 [`TAXONOMY--v1.0.yaml`](../../knowledge-base/20_knowledge_cards/TAXONOMY--v1.0.yaml) 为准；每条只落一个主域，跨域只记相关域。不能由文件目录或标题单独定域，至少核对正文及来源定位；不可读或证据不足时保持待审并登记例外。
- `authority_level`、`sensitivity`、`availability` 和 `flow_disposition` 按现行来源治理字段逐条给值。缺少原始出处不推断权威级别；含内部企业/个人/合同/经营数据的来源从严标注并禁止进入产品候选，AI 未核验摘要不得采纳。此批次的输入清单、全量文本和指纹留在 ObsidianWiki，本仓只存定位、分类、证据引用和必要处置摘要。
- HIGH/MED/LOW 采用已有规格定义的审阅级别；先用来源类型、知识地图关系和已有覆盖信息形成可复核优先级，再检查正文，记录 `source_id`、输入快照、审核级别、字段结论、证据定位、审核状态与例外原因。不能从标题关键词直接宣称已全文审阅；HIGH 全量读，MED/LOW 按规格双审抽样并检查误差集中度。
- 每批次先写入独立批次文件并运行 coverage validator；按 source ID 闭合核对，未覆盖条目不得进入 adopted/candidate。semantic batch 合并前复核快照指纹；每批提交后更新知识库 inventory/checksum、路线图与交接，再继续下一批。候选 seal 及 `CURRENT_RELEASE` 变更仍遵守原有独立 reader 和用户战略裁决门槛。

## 全轨退出条件

- 三仓库身份、内容哈希、coverage、失败清单和敏感边界可重放；
- accepted working-tree manifest 的双指纹一致、来源四维 diff、独立 reader 和 sealed lock 全通过；
- 用户逐项裁决，activation commit 的干净 worktree、门禁和远端 CI 全绿。

详细步骤见[统一完整实施计划 K 轨](../../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md#10-k第二代静态知识刷新与战略重基线)。


## 2026-10-26 队首启动记录

K3 是当前唯一执行项。首个只读复核发现 accepted manifest `obsidianwiki-k2-2026-10-19-final.json` 与当前 vault 状态不匹配：HEAD/tree 仍为 `e04d6833` / `aa7d84d3`，但 dirty 路径从 1,377 变为 1,434，当前 porcelain SHA-256 `d2535e6478caaadee622e3551a730335ec273f46d68e5f2fdb9d92096bf8dfed`（两次读取一致），旧 manifest 状态 SHA 为 `c688b336f3cd86c84e3f40874838e0c1083db75b201cde2985cee4cc10f35fdc`。ObsidianWiki `.davybase/image_evidence` 最近文件时间为 2026-10-25；未发现活动 Davybase/Obsidian 任务进程。故旧 K3 baseline/diff 仍是其 10 月 19 日 accepted 截面的历史有效结果，但不作为当前正文审阅输入。已在 vault 外重新冻结并接受 10-26 快照：候选/复验内容 SHA `c84efd671e2b90e4f69152c3dd04a570d9c378d08fb7a3cb97b86e322f123df0` 一致、写句柄 0；manifest 已随 Davybase `f65df69` 推送并释放锁。registry/baseline/delta/cumulative diff 均已生成；14 项 source baseline/coverage tests 通过，生成结果可逐字节复现，生成后 fingerprint 与 accepted snapshot 一致。当时下一步为逐条主题路由与 HIGH 全文审阅；该步骤已开始，最新进度见本文件上方当前状态与各批次台账。ObsidianWiki 不写入，`CURRENT_RELEASE` 不变。


### K3 语义审阅批次 003

第三批完成 A-finance HIGH 簇 7 的三篇全文本地审阅，覆盖三表勾稽、现金流分析、资产负债表分析。三条来源哈希均匹配 accepted snapshot；路由 K1/K2，处置仍为 pending-verification。审阅发现现金流桥算例不闭合，现金流指标阈值/行业判断待验证，部分资产负债表原则概括过度且 ROE/EVA 定义不完整。详见来源层 [`semantic-review-2026-10-26-batch-003.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-003.tsv)。


### K3 语义审阅批次 004

第四批完成 A-finance HIGH 簇 7 的三篇全文本地审阅，覆盖现金流分析与报表编制。三条哈希均匹配 accepted snapshot；分析方法路由 K2、编制流程路由 K1，处置仍为 pending-verification。两篇分析文章的阈值缺少定义/数据依据/适用边界，编制笔记关于报表精度的表述不可靠，需正式准则与原始材料复核。详见 [`semantic-review-2026-10-26-batch-004.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-004.tsv)。


### K3 语义审阅批次 005

第五批完成 A-finance HIGH 簇 7 的三篇全文本地审阅，覆盖报表勾稽、合并报表与资产负债表分析。三条哈希均匹配 accepted snapshot；路由 K1/K2，处置 pending-verification。合并案例账表不平衡且抵消数无依据；通用勾稽描述与指标阈值需按正式准则、适用边界和原始材料复核。详见 [`semantic-review-2026-10-26-batch-005.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-005.tsv)。


### K3 语义审阅批次 006

第六批审阅合并报表成本法编制、集团内部交易抵消和合并抵消实践三篇全文本地笔记。三条哈希匹配 accepted snapshot，均路由 K1、pending-verification。重点记录来源规范依据不足、抵销金额与损益归属分配概念混用、示例省略购买日计量等前提。详见 [`semantic-review-2026-10-26-batch-006.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-006.tsv)。


### K3 语义审阅批次 007

第七批审阅三表勾稽文章与两篇知识库短摘要，共 3 条全文本地读取，均路由 K1、pending-verification。记录案例现金与营运资本信息不全、正负现金流判断无场景边界、摘要与既有来源主题重叠等限制。详见 [`semantic-review-2026-10-26-batch-007.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-007.tsv)。


### K3 语义审阅批次 008

第八批审阅 3 篇 HIGH/K6 资金预测材料，均为全文本地读取，哈希匹配快照，均 pending-verification。方法论缺实测预测证据，模型公式/覆盖边界不完整，另有两篇模型说明高度重叠，待原件核对重复关系。详见 [`semantic-review-2026-10-26-batch-008.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-008.tsv)。


### K3 语义审阅批次 009

第九批审阅资金缺口测算两篇和财报先行指标一篇，均全文本地读取、哈希匹配，路由 K6、pending-verification。监管周转公式已查官方现行来源，限于银行贷款需求测算示例；两篇五模型文章疑似重复；报表先行信号没有量化预测证据。详见 [`semantic-review-2026-10-26-batch-009.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-009.tsv)。


### K3 语义审阅批次 010

第十批审阅净利润与现金流关系 3 篇，均全文本地读取、哈希匹配 accepted snapshot，路由 K2，pending-verification。发现现金流防舞弊断言过度绝对、案例现金收支未闭合且混淆负债余额与现金缺口、调节公式不是完整报表公式。详见 [`semantic-review-2026-10-26-batch-010.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-010.tsv)。


### K3 语义审阅批次 011

第十一批审阅 1 篇净利润与现金流管理文章，全文本地读取、哈希匹配 accepted snapshot，路由 K2，pending-verification。与同账号旧文高度重叠但可能为更新版，未据此合并；现金流质量/周转阈值缺少出处，公式与指标边界不完整。详见 [`semantic-review-2026-10-26-batch-011.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-011.tsv)。


### K3 语义审阅批次 012

第十二批审阅内控五流、收入确认与凭证证据链 3 篇，均全文本地读取、哈希匹配 accepted snapshot，路由 K1，pending-verification。记录内控与税会规则概括过度、原文准则版本/适用场景未核验，以及凭证清单不能当作统一法定要求。详见 [`semantic-review-2026-10-26-batch-012.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-012.tsv)。


### K3 语义审阅批次 013

第十三批审阅自动计费/付款资料 1 篇，全文哈希匹配 accepted snapshot，路由 K7。因原文含可识别第三方合同、付款和账户信息，按 project-internal 标注、处置 rejected 并排除产品候选；仓内只保留定位和最小化风险摘要，不复述敏感明细。详见 [`semantic-review-2026-10-26-batch-013.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-013.tsv)。


### K3 语义审阅批次 014

第十四批审阅 AI 财务应用、业财模型、运营到财务映射及综合分析框架 4 篇全文，哈希匹配 accepted snapshot，均 pending-verification。记录促销材料缺少独立效果证据、模拟/样例数值没有出处、映射和模型缺少定义/公式/边界等限制。详见 [`semantic-review-2026-10-26-batch-014.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-014.tsv)。


### K3 语义审阅批次 015

第十五批审阅 3 篇财务能力看板与动态指标交互材料，均全文读取、哈希匹配 accepted snapshot，路由 K5/K3/K8，pending-verification。发现阈值冲突且无行业依据、匿名示例无原始数据、DAX 会计公式过度简化和时间/汇率上下文不足。详见 [`semantic-review-2026-10-26-batch-015.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-015.tsv)。


### K3 语义审阅批次 016

第十六批审阅自动导入财务看板两篇和 PPT 汇报框架一篇，均全文读取、哈希匹配 accepted snapshot，路由 K5/K4，pending-verification。两篇自动看板文本高度重复且缺少模型实物与公式验证；PPT 页面/图表框架缺原始数据和已验证模板，不能视为实证案例。详见 [`semantic-review-2026-10-26-batch-016.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-016.tsv)。


### K3 语义审阅批次 017

第十七批审阅纯本地经营驾驶舱、集团财务智能驾驶舱及 Power BI 看板 3 篇全文，均哈希匹配 accepted snapshot、pending-verification。前两篇功能/离线安全为文章自述，无原型验证；集团案例有子公司排名错误且来源未证，Power BI 样例声明为模拟数据，仅作图表结构参考。详见 [`semantic-review-2026-10-26-batch-017.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-017.tsv)。


### K3 语义审阅批次 018

第十八批审阅同源《企业管理报表.xlsx》记录两条，正文哈希匹配 accepted snapshot。根据标题/原文 URL 合并一条知识库副本为 `duplicate`；另一条保留 pending-verification。实际 XLSX 未在快照中，表格/公式/勾稽均未实测；AI 派生图像说明未作为原始证据。详见 [`semantic-review-2026-10-26-batch-018.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-018.tsv)。


### K3 语义审阅批次 019

第十九批对内部业财实践簇 9 条 HIGH 资料作最小元数据筛查，未展开内容审阅。因来源定位表明包含企业内部规划、指标、架构或主数据内容，统一标为 project-internal/rejected、排除产品候选，具体事实不复制到本仓。详见 [`semantic-review-2026-10-26-batch-019.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-019.tsv)。

第二十批审阅 3 篇 HIGH/簇3 经营分析方法文章，全文哈希匹配 accepted snapshot，均 pending-verification。闭环、三问和问题—根因—建议结构可作追问模板；其中示例数据、>2σ 阈值、节省比例、ROI 与案例效果没有原始数据或独立证据，不作为产品规则或实证。详见 [`semantic-review-2026-10-26-batch-020.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-020.tsv)。

第二十一批审阅 3 条 HIGH/簇3 来源：三张底牌文章全文哈希匹配且标记无来源 KPI/效果为待验证；发现同源微信副本后将候选副本标为 duplicate；半年度工作总结/计划报告因可能含内部经营数据，只检查元数据并标 project-internal/rejected，未打开正文。详见 [`semantic-review-2026-10-26-batch-021.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-021.tsv)。

第二十二批审阅 3 篇 HIGH/簇3 全文。两篇不同日期和 URL 的同题业务逻辑文章内容高度相似，但发布关系未核实，保留为独立 `pending-verification`；乳制品/制造业案例及业务穿透文章中的数值、阈值与成效无独立依据，不作事实或产品规则。详见 [`semantic-review-2026-10-26-batch-022.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-022.tsv)。

第二十三批审阅核算粒度、财务经营思维及降本增效汇报三篇 HIGH/簇3 全文。案例业绩、ROI/阈值和所谓已验证效果均无来源数据；多账套、影子账套等做法需按法定核算和系统约束验证。文章只作为待验证框架，不形成通用流程或实证结论。详见 [`semantic-review-2026-10-26-batch-023.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-023.tsv)。

第二十四批审阅 2 条 HIGH/簇3：闭环案例 Getnote 笔记与 wechat-72e4a10ae09e 内容高度相似，但原文关联未核且 URL 不可用，保留 pending-verification、不作 duplicate；经营驱动树文章全文核阅并保留 pending-verification，未核验的示例数字、FineBI 看板主张不作事实。详见 [`semantic-review-2026-10-26-batch-024.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-024.tsv)。

第二十五批对 3 条簇2 内部业财架构/讨论/支出归集资料只做元数据筛查，未打开正文，统一标 project-internal/rejected。旧 A-finance 高优先级清单中的“AI财务2026Q3”路径经 ObsidianWiki Git 元数据追溯：提交 `c743b98972d45794d5948787ab65e7fd9afcbad1` 删除旧财务路径，同一 tree 中系统架构新路径指向相同 blob `2b4dd69c5505711c6b2ea3b4fa5fa4a6d1aebcc3`。新路径不在当前 accepted baseline，故作为基线外迁移从当前 coverage 候选中排除；正文未打开，不计入 76 条 HIGH 审阅。此项路径迁移关系已闭合，来源是否纳入产品知识仍不在本轮结论内。详见 [`semantic-review-2026-10-26-batch-025.tsv`](../../knowledge-base/10_sources/semantic-review-2026-10-26-batch-025.tsv) 与当前快照报告。第二十六至三十一批完成旧 W1 MED 队列双审，完成 17/17 条（前 9 条之外，新增财务业务思维、盈利能力分析、酒店经营分析）。均为公开二手材料，保留 MED/pending-verification；京东分部收入相加高于合并净收入 181.5 亿元；数据驱动看板优先级计数 28,155 高于总量 26,935，占比合计约 104.6%；均未核原始出处前不得作为产品事实。制度/流程二分法不作为权限或合规设计依据；Power BI 价格/功能和AI替代就业预测不得当作当前事实；盈利分析公式错误不得直接定义指标，酒店GOP及案例口径须核验。coverage 台账覆盖 9,673 个 source_id：routed 81、filtered 16、pending_review 9,576。第31批三条绩效材料均为 pending-verification：绩效模板的时间/阈值与评分口径不一致，营销分析复用图表的公式/权重口径冲突，匿名共享中心案例缺原始样本与统计方法且包含未证实的因果判断；不作制度或产品事实。


### K3 语义审阅批次 032

从 W3 MED 分层首批抽审三条全文来源；正文哈希与 accepted baseline 一致，均保留 pending-verification。回归教程将相关性误说成数据分析本质、以固定 R 阈值和 p 值作普适判断，广告样本数据不完整；波特五力文章的外卖时点案例与投票图不能验证市场进入决策；门店策略评估只有前后期比较、无对照及混杂控制，且多个期间/增长率口径不一致。以上内容只记录为方法框架或待验证案例，不作产品事实。coverage 更新至 routed 81、filtered 16、pending_review 9,576。详见来源批次台账。


### K3 语义审阅批次 033

W3 MED 第二组抽审三条全文：电商直播运营驾驶舱、零售经营分析框架、零售经营看板。哈希均匹配 accepted baseline；全记 pending-verification。电商驾驶舱指标语义、统计分母、周期和原始数据未充分提供；零售框架未提供经验证的效率提升/预测结果；两篇 2024-08 零售文结构与段落高度相似但来源 URL、发布日期不同，保留独立记录并待核原稿关系，不强行去重。正文与 AI 派生附录区分处理，派生指标不作事实。coverage 更新为 routed 84、filtered 16、pending_review 9,573。


### K3 语义审阅批次 034

W3 MED 第三组抽审三条全文：零售“人货场”落地模板、BI与财务分析科普、零售多场景看板。源文件指纹与 accepted baseline 一致，均为 pending-verification。人货匹配可作历史数据分析路径，但缺少季节、库存、促销和原始订单等条件时不能当未来需求预测；BI定义与厂商功能/安全比较属概括及推广内容；女装RFM、购物篮及多板块看板缺工作簿和原始数据，派生图表数值不作证据。coverage 更新至 routed 87、filtered 16、pending_review 9,570。


### K3 语义审阅批次 035

W3 MED 第四组抽审三条全文，哈希与 accepted baseline 一致，均保留 pending-verification。零售B2B看板明确使用省份/国家映射与随机目标，案例数据及排行均为演示加工值；业财一体化文聚焦流程和系统协同，但“95%”及工具能力、收益无独立证据；零售五场景文章的ABC占比、活动效果及实时/多源工具主张未提供可复算数据或原始模型，均不形成事实或产品规则。coverage 更新为 routed 90、filtered 16、pending_review 9,567。


### K3 语义审阅批次 036

W3 MED 第五组抽审三条全文，源 SHA 与 accepted baseline 一致，处置均为 pending-verification。电商指标清单中周转率/周转天数、销售/库存计量口径及成交率分母需重定义；新品拓客案例使用脱敏企业与虚拟品牌样本，分群与目标合理性无法独立复算；房地产经营案例缺少可核工作簿、数据来源和对照，观察性分析不足以证因果或支撑投资建议。coverage 更新为 routed 93、filtered 16、pending_review 9,564。
