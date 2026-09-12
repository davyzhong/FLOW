---
doc_id: FLOW-VERIFY-DOCMIG-001
title: 文档与静态知识迁移验证记录 v1（M0–M6）
doc_type: verification
status: verified
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
commit_refs: "[6f3e90e, 2016306, dd5a24b, 0fc3488, d461ea2, a99a5b2, 063b9ea, 249ef22, 938d3ac, 7567e0a, 962b651, 970b864, df7f6e3, d9c391b, 99e6091, c7bb935, 2f48df4, e3640aa, 1a4d009]"
evidence_refs: "[make-docs-check, reader-test-RUN-2, release-lock]"
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: repository
supersedes: []
superseded_by: null
---

# 文档与静态知识迁移验证记录（M0–M6 全批次）

## 门禁结果（make docs-check，最终态）

| 门禁 | 结果 |
|---|---|
| 元数据合同 | PASS（183 docs / 94 legacy-exempt / 0 errors；唯一 current state） |
| M0 基线重放 | PASS（checkpoint tree 可重放） |
| 来源基线 | PASS（3317 条 vault git tree 对账） |
| 知识发布 | PASS（flow-knowledge-2026-09-12.1，31 资产 SHA-256 校验） |
| 全库链接 | PASS（0 断链；历史档案豁免登记于 link-allowlist.tsv） |
| 测试 | PASS（63 项，含 fail-closed 负例） |
| 无上下文接续 | PASS（RUN-2 5/5，critical 零错；RUN-1 失败证据保留） |
| Obsidian 脱离 | PASS（双轮盲测仓库内闭合） |

## 批次验收摘要

M0 基线冻结（2740 文件清单/405 不可变锁/367 消费者/path-map 2341 全处置）→ M1 治理工具与唯一入口（元数据合同+CI、D001–D051 拆分、唯一 current state）→ M2 静态知识发布（12 组来源对账、16 卡+11 手册+taxonomy+映射 canonical、release lock 31 资产）→ M3 产品/规格统一（六份产品定义+冲突矩阵、SPEC_INDEX 15 规格、架构五文档、机器消费者 21 测试）→ M4 唯一路线图（CURRENT_ROADMAP+4 工作包+三视图）→ M5 历史整理（18 计划归档、顶层收口、生成式状态、keep 化处置修订）→ M6 总门禁（links/rubric/CI m6 化、五题盲测两轮）。

## 已知边界（非阻塞）

- 兼容入口删除条件（消费者清零+两个发布周期）未到期，全部保留；
- implementation/ 非机器部分判 keep（验证记录与提交绑定）；
- Q3 的知识库入口未列入五份起点文档（RUN-1/2 改进项，下次 READING_ORDER 修订时考虑）。

## 执行期修正（前向提交，无历史重写）

链接改写误伤与层级修复（f5099eb）、字节冻结档案恢复+allowlist（63c8ed1）、豁免漂移批量合规化、负例测试 fixture 化（e3640aa）、Q4 权威文档补全（1a4d009）。
