---
doc_id: FLOW-RESEARCH-DAVYBASE-IMAGE-BATCH-K0-001
title: Davybase 微信图片知识化批次回顾性验收
doc_type: research-synthesis
status: verified-with-limitation
version: 1.0
created_at: 2026-10-17
updated_at: 2026-10-17
owner: FLOW
depends_on: [FLOW-WI-KNOWLEDGE-REFRESH-V2-001]
acceptance_refs: [FLOW-PLAN-INTEGRATED-EXECUTION-20260924, FLOW-DESIGN-KNOWLEDGE-REFRESH-002]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: knowledge-system
---

# Davybase 微信图片知识化批次回顾性验收

## 结论

对历史 Git 输出快照重新核算后，1,265 篇输入的严格终态为 1,239 篇成功、2 篇待复核、
24 篇装饰图过滤。历史 `done=true` 的 1,241 篇中有 2 篇各记录 1 张失败图片，不能将其
计为严格成功。机器清单 strict 对账通过；32 篇确定性分层样本及 512 张图片的正文哈希、
图片顺序、来源定位、字节数和内容哈希均与清单一致。

此结论仅证明历史计数和内容快照可复核。原运行未保存 prompt SHA-256，因此 1,265 篇均
标记为 `nonconformant`，不符合 L1 完整来源要求。FLOW 当前 release 仍为
`flow-knowledge-2026-09-12.1`，本次没有修改 ObsidianWiki。

## 可追溯证据

| 项目 | 标识 |
|---|---|
| Davybase 分支 | `codex/knowledge-run-manifest-k0` |
| 实现提交 | `172a0990980ebe7494322f122302ee0dd6f61876` |
| 证据提交 | `94fc05d` |
| 最终交接/统计提交 | `eb8c3d0` |
| 历史输入提交 | `632ba15080e48e4ce5bd287b31896c808025b726` |
| 历史输出提交 | `4b000369c392730ca706f9cd86f3e861854fbfbf` |
| pre-K1 HEAD/tree | `e04d6833a623033a3601d36192f02dc15184eb6e` / `aa7d84d3fff59b0c1dd390fc872beb66cba40f52` |
| Obsidian dirty 路径数 | 1,365 |
| 微信范围 SHA-256 | `0a42346d276917c8b94f1b0c198ca5bfd68405c35c1656407bc10135e236c7f7` |
| 运行清单 SHA-256 | `c603baab83f7873c852681c69dfb314e7004e43b230ea832fb2a1e9043ce26bc` |
| 抽样审计 SHA-256 | `d638580d88fe75fe4f58ca5320c5ebe53ab40d455f9674954f5de38430e497be` |

详细 JSONL 清单、抽样记录及终态说明保存在 Davybase 分支
`codex/knowledge-run-manifest-k0` 的 `docs/evidence/`。实现 SHA 的本地 pytest 为 872 项，
Ruff、README 统计及链接检查通过；GitHub 对该 SHA 未运行 `ci.yml`，README 截图工作流
成功不作为测试 CI 证据。

## 下一步

K0 已关闭。唯一后续子步 K1 从只读盘点企业管理、财务与会计、跨境物流三个范围的图片覆盖
开始，先核对 allowlist、异常和候选 pathspec。ObsidianWiki 已有的 1,365 条变化保持只读；
在覆盖结果及输入仓库安全条件确认前，不执行图片 apply、暂存或 release 切换。
