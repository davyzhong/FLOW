---
doc_id: FLOW-WI-KNOWLEDGE-REFRESH-V2-001
title: 第二代静态知识刷新与战略重基线
doc_type: work-item
status: active
version: 1.6
created_at: 2026-09-24
updated_at: 2026-10-19
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
- K0/K1/K2 已完成，K3 为当前唯一队首。K2 accepted working-tree manifest：ObsidianWiki `main@e04d6833`、1,377 条 dirty 路径、111,912 个文件/4,240,118,843 字节；HEAD/tree、Git 状态与完整内容 SHA 的候选/复验值一致，真实可写句柄均为 0。Davybase 冻结器/远端浅校验/accepted 证据提交 `ea04578`、`c057acb`、`57c4738` 已推送。详细报告见[FLOW K2 验收](../../60_delivery/verification/2026-10-19--k2-working-tree-snapshot-v1.md)，ObsidianWiki 未修改。K3 读取前与构建后都要复核来源指纹；若任何源变化，不继续当前 candidate。K4–K6 与战略裁决仍未完成。
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

按已批准 Task K3 执行：以 Davybase accepted manifest 为来源凭据，先复核 ObsidianWiki 当前 HEAD/tree/status/content 指纹；生成期间保持只读，完成后再复核同一指纹。输入稳定后，按已版本化 source-inputs / source-id-registry 规则生成新增、删除、重命名、正文变化与 enrichment 四维 diff，运行 allowlist 全量路由、HIGH 全量精读、MED/LOW 双审与错误集中度检查；通过全量 coverage 后构建 draft candidate。逐项验收、工具和目标文件见统一实施计划 Task K3。不得清洗/提交 ObsidianWiki，不得替用户 seal activation 或修改 `CURRENT_RELEASE`。

## 全轨退出条件

- 三仓库身份、内容哈希、coverage、失败清单和敏感边界可重放；
- accepted working-tree manifest 的双指纹一致、来源四维 diff、独立 reader 和 sealed lock 全通过；
- 用户逐项裁决，activation commit 的干净 worktree、门禁和远端 CI 全绿。

详细步骤见[统一完整实施计划 K 轨](../../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md#10-k第二代静态知识刷新与战略重基线)。
