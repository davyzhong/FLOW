---
doc_id: FLOW-WI-KNOWLEDGE-REFRESH-V2-001
title: 第二代静态知识刷新与战略重基线
doc_type: work-item
status: active
version: 2.0
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
- K0/K1/K2 已完成，K3 当前实际执行。FLOW 的实际资料源是 ObsidianWiki；Davybase 只在 K0–K2 的历史工具链中承载过扫描/快照工具及一次性证据，不构成 FLOW 代码、运行时或产品依赖。K2 accepted working-tree manifest：ObsidianWiki `main@e04d6833`、1,377 条 dirty 路径、111,912 个文件/4,240,118,843 字节；HEAD/tree、Git 状态与完整内容 SHA 的候选/复验值一致，真实可写句柄均为 0。K3 读前复核已通过，Obsidian 当前 HEAD/tree/status/content SHA、文件数与字节数均与 accepted manifest 一致，可写句柄 0。当前后续仍限于只读 baseline/diff，生成后再做来源指纹复核。详细 K2 报告见[FLOW K2 验收](../../60_delivery/verification/2026-10-19--k2-working-tree-snapshot-v1.md)，ObsidianWiki 未修改。K4–K6 与战略裁决仍未完成。
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

2026-10-19 accepted manifest `obsidianwiki-20261019T075638+0800-0c0ac842`（SHA-256 `b7e566e68b1119117999fc9ef08f7fae657e6bcbc3d3482d77ea56caf0e44654`）为历史输入。10-26 检出当前 dirty 路径已变，故新取稳定快照；当前 K3 输入改为 snapshot `obsidianwiki-20261026T003619+0800-4ea1c067`（manifest SHA-256 `ede08faabcf5c70222fec7c628f9ae778deba82dbdf5bdab26ad154184269e39`），详情见[当前快照复核](../../60_delivery/verification/2026-10-26--k3-current-snapshot-v1.md)。

10-19 K3 自动来源基线与四维差异已完成，结果（allowlist 9,671 篇，universe 9,956 条）仅适用于 10-19 accepted snapshot，见[历史来源基线验收](../../60_delivery/verification/2026-10-19--k3-source-baseline-v2.md)。当前要以 10-26 snapshot 重新构建 registry/baseline/diff，生成前后确认指纹一致；不复用旧数据冒充当前结果。实现包含 `build-v2` 和严格 coverage 闭合校验器。

**当前子步仍属 K3，未完成整轨验收**：逐条主题路由和 HIGH 全文审阅、MED/LOW 双审抽样、错误集中度检查、coverage/例外闭合、知识综合和独立 reader 尚待完成。旧 2026-09-12 baseline 没有完整历史改名 registry；本轮以精确路径迁移旧 ID，未匹配项记为新增/删除，不用标题相似度推断改名。不得据此声称“没有改名”。`CURRENT_RELEASE` 仍为 `flow-knowledge-2026-09-12.1`，未 seal、未激活。

## 全轨退出条件

- 三仓库身份、内容哈希、coverage、失败清单和敏感边界可重放；
- accepted working-tree manifest 的双指纹一致、来源四维 diff、独立 reader 和 sealed lock 全通过；
- 用户逐项裁决，activation commit 的干净 worktree、门禁和远端 CI 全绿。

详细步骤见[统一完整实施计划 K 轨](../../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md#10-k第二代静态知识刷新与战略重基线)。


## 2026-10-26 队首启动记录

K3 是当前唯一执行项。首个只读复核发现 accepted manifest `obsidianwiki-k2-2026-10-19-final.json` 与当前 vault 状态不匹配：HEAD/tree 仍为 `e04d6833` / `aa7d84d3`，但 dirty 路径从 1,377 变为 1,434，当前 porcelain SHA-256 `d2535e6478caaadee622e3551a730335ec273f46d68e5f2fdb9d92096bf8dfed`（两次读取一致），旧 manifest 状态 SHA 为 `c688b336f3cd86c84e3f40874838e0c1083db75b201cde2985cee4cc10f35fdc`。ObsidianWiki `.davybase/image_evidence` 最近文件时间为 2026-10-25；未发现活动 Davybase/Obsidian 任务进程。故旧 K3 baseline/diff 仍是其 10 月 19 日 accepted 截面的历史有效结果，但不作为当前正文审阅输入。已在 vault 外重新冻结并接受 10-26 快照：候选/复验内容 SHA `c84efd671e2b90e4f69152c3dd04a570d9c378d08fb7a3cb97b86e322f123df0` 一致、写句柄 0；manifest 已随 Davybase `f65df69` 推送并释放锁。当前下一步是使用新 snapshot 重建 K3 registry/baseline/diff，并在构建后复核指纹；随后开展语义路由与审阅。ObsidianWiki 不写入，`CURRENT_RELEASE` 不变。
