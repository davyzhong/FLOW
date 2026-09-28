---
doc_id: FLOW-VERIFY-PUBLIC-ROW-IDENTITY-20260929-001
title: 公开财报行身份范围修订与全链验收
doc_type: verification
status: draft
version: "1.0"
created_at: 2026-09-29
updated_at: 2026-09-29
owner: FLOW
commit_refs: "[af6c0672]"
evidence_refs: "[row-identity-map-40-rows-79-values, l1-v5-1776-of-1776, isolated-l0-1532-of-1532, isolated-l1-db-match-zero, p5-facts-670-content-sha-stable, statement-api-tests-80-of-80, scripts-tests-138-of-138, docs-m1-299-zero-errors, links-zero-errors]"
applies_to: public-analysis
supersedes: []
superseded_by: null
---

# 公开财报行身份范围修订与全链验收

## 结论

已将经逐格裁决确认的来源行身份/范围补充为版本化覆盖层，不改原 PDF、历史基础抽取 YAML 或数值。阿里现金流合并范围、阿里流动资产限定、菜鸟非流动资产/负债限定均由同一 fail-closed 适配器服务于导入和 L0/L1；JDL 身份沿用已交付的 v3 修订。BABA FY2020 评审 bundle 中 28 个虚构 `value_current` 别名不作为产品数据写入。

## 验收身份

| 项目 | 值 |
|---|---|
| 代码基线 | `af6c0672f42ad36cc9e0ea6b7ecf539b8d1c0e1a`（本次实现尚待提交） |
| 数据库 | 新建隔离 Compose project `flowcverify`，宿主端口 55432，数据库 `flow`；未连接常驻项目数据库 `flow`，也未写旧 `flow_test` |
| Schema | 使用既有迁移至 `0031_enterprise_directory`；没有新增迁移或修改 schema |
| 报告数据 | `seed_p5_statements.sh` 加载 5 家公司、14 份报告 |
| 源文件 | 修订映射逐行校验 PDF SHA-256，逐行核对源项目、期间值与来源页 |

## 结果

| 检查 | 结果 |
|---|---:|
| 版本化行身份映射 | 40 条来源行、79 个真实候选值；生成器重建与文件完全一致 |
| L1 v5 | 1776/1776 页级锚；strong 1022、weak 735、sign-flip 15、visual 4；未定位 0 |
| 隔离 L0 | 1532/1532 一致；差异、缺失、多出均为 0 |
| 隔离 L1 数据库对账 | 1776 条，锚失效 0、值不一致 0、未入库 0 |
| P5 派生事实 | 670 条；重建文件 SHA-256 与变更前一致（`50d17f832834adc1e46558d5fa3a3b6879afb5e4957538cc1b5729428f822e46`） |
| API 财报测试 | `tests/statements` 80/80；新增行名元数据导入测试 1/1 |
| 脚本测试 | 138/138 |
| 文档与格式 | Ruff（排除既有未执行 shebang 的 EXE001）通过；M1 299 份文档、0 错误；链接 0 错误；diff check 通过 |

GitHub CI 必须在本交付提交后按准确 SHA 再确认；此前 `af6c0672` 的 CI run `36468667953` 与 `36472291231` 均已 success，但不能替代本提交 CI。C 级出口仍未通过：独立 oracle、盲评、holdout 和最终 Go/No-Go 尚未验收。
