---
doc_id: FLOW-SOURCE-REFRESH-PREFLIGHT-20260918
title: 第二代静态知识刷新执行前置基线
doc_type: source-evidence
status: registered
version: 1.0
created_at: 2026-09-18
updated_at: 2026-09-18
owner: FLOW
snapshot_id: preflight-2026-09-18T06-31+08-00
sensitivity: internal
---

# 第二代静态知识刷新执行前置基线

本记录固定 Task 0 开始时的三仓库身份和已知事实。它不是 K2 的 15:00 来源截面，也不替代后续 K0 机器验收。

## 1. FLOW

- canonical remote：`https://github.com/davyzhong/FLOW.git`
- 执行分支：`codex/knowledge-refresh-v2`
- base commit：`5ee50ff053f72fb73a6cc4a36907cda885806222`
- base tree：`b5ed9e4259673685dc41e31b163d3aeb5a6164b6`
- current knowledge release：`flow-knowledge-2026-09-12.1`
- Task 0 采集时工作树变化：仅本任务新增实施计划；无已知范围外修改。

## 2. Davybase

- canonical remote：`git@github.com:davyzhong/davybase.git`
- 分支：`main`，与 `origin/main` 一致
- commit：`1db9e3d1d7c10171db408b8a9d5886fd74342680`
- tree：`20c5816fad4319639a9071a37dd40af5f9cd308c`
- 工作树：clean
- 图片批次上游声明：1,265 篇输入中 1,241 篇完成图片知识化，24 篇只有装饰图而正确跳过；该数字来自提交 `b988f0e6b0d718852f35900a35135c892455d981` 及后续 HANDOFF，仍须在 K0 通过逐项重算、抽样和 retrospective manifest 验收。
- 当前已知合同缺口：图片指纹仍以名称和大小生成 SHA-1；图片工具仍以微信账号为主要入口；旧批次没有完整统一的 run manifest。这些缺口由 Task 1–3 处理，不能反向伪造旧批次 provenance。

## 3. ObsidianWiki

- canonical remote：`git@github.com:davyzhong/ObsidianWiki.git`
- 分支：`main`，与 `origin/main` 一致
- commit：`632ba15080e48e4ce5bd287b31896c808025b726`
- tree：`0edf2eb77b4ec85309452e3aebd8bfd6192e49c9`
- 提交时间：`2026-09-18T01:51:26+08:00`
- 工作树：clean
- tracked files：54,057；该数只用于前置环境说明，不是新 release 分母。
- 本 commit/tree 不是 K2 正式截面。正式截面必须在 K1 受控写入提交推送后，按 14:30/15:00/15:30 排他锁合同重新取得。

## 4. 规格和审查状态

- 批准规格：`FLOW-DESIGN-KNOWLEDGE-REFRESH-002` v1.1。
- 实施计划：`FLOW-PLAN-KNOWLEDGE-REFRESH-002` v1.1。
- 规格独立复审：P1=0、P2=0。
- 实施计划独立复审：经过三轮阻断性修订后 P1=0、P2=0；已关闭 K0/K1 顺序、动态截面日期、冻结历史决策、sealed 不可变、最终 SHA 复验、coverage 停止条件和独立读者门禁等问题。

## 5. 当前授权边界

用户已批准安全规格并明确要求开始实施。该授权覆盖 K0–K5 和 S0 的准备与证据工作；S1 仍是正式人工裁决门，不能用本次“开始实施”替代未来对具体战略建议的接受、修订、拒绝或后置决定。产品代码不在本轮授权范围内。
