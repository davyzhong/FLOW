---
doc_id: FLOW-VER-CFO-ENTERPRISE-PACKAGE-LINEAGE-20261018
title: 大麦企业发行包血缘与整数数量验收
doc_type: verification
status: draft
version: 1.0
created_at: 2026-10-18
updated_at: 2026-10-18
owner: FLOW
evidence_refs: [enterprise-package-tests-7, damai-release-manifest-tests-7, enterprise-package-deterministic-build]
applies_to: data-package
---

# 大麦企业发行包血缘与整数数量验收

## 结论

工作包 7a 第 4 阶段子步 4.5 已完成。大麦企业发行包由正式构建器从 `fixtures/damai/` 重建，发行数据与当前源 fixture 一致；订单数和件量保留整数语义。全过程未连接或修改常驻数据库。

## 发现与修复

旧发行包 `data/enterprise/damai-logistics/v2` 的 `source_manifest_sha256` 落后于源 fixture，且 `operating_actuals.jsonl` 的 1,920 条订单/件量记录仍是旧比例分摊小数。发行包原校验只核包内 manifest 自洽，未检查来源清单与实际源数据的一致性。

`build_enterprise_data_package.py verify` 现在会：

- 核对发行包记录的源 manifest SHA-256 与当前 `fixtures/damai/manifest.json`；
- 核对 `canonical`、`statements`、`operations`、`forecast`、`workbooks` 五个源目录的文件集合和逐文件字节内容；
- 继续核验包内文件 SHA、字节数、JSONL 行数、组织引用与生成 SQL。

发行包 README 已说明血缘校验与整数计数约定。重建使用项目正式生成器，没有手工改写经营数字。

## 验收证据

- `uv run --project services/api python scripts/build_enterprise_data_package.py build`：成功；31 个发行文件。
- `uv run --project services/api python scripts/build_enterprise_data_package.py verify`：成功；31 个文件通过校验，组织样本为 8 部门/单元、8 岗位、8 身份和 146 权限映射。
- `operating_actuals.jsonl`：1,920 行；发行文件与源文件逐字节相同；`order_count` 和 `shipment_count` 均无非整数值。
- 连续两次构建后的发行目录摘要均为 `cb85fd785d6b983fe0f615999c875eb1fb4cada3918e29fe62165f6ff40832c2`，重建确定。
- `scripts/tests/test_enterprise_data_package.py` 与 `scripts/tests/test_verify_damai_demo.py`：14 项通过；覆盖过期源指纹拒绝、发行数据漂移拒绝、整数语义与现有演示清单校验。
- `ruff check scripts/build_enterprise_data_package.py scripts/tests/test_enterprise_data_package.py`：通过。
- 文档门禁 M1：通过（331 篇文档、89 项历史豁免、0 错误）。

## 边界

本验收不读取数据库，不生成新的公开财务事实，不把 synthetic allocation 改写成公开披露值。公开年度数据与合成月度分配继续依据既有数据合同分层。截图工作流继续暂停。
