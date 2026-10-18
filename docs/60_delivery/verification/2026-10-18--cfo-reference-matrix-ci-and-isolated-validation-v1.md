---
doc_id: FLOW-VER-CFO-MATRIX-CI-20261018
title: CFO 参考模块覆盖矩阵 CI 与隔离验收记录
doc_type: verification
status: draft
version: 1.0
created_at: 2026-10-18
updated_at: 2026-10-18
owner: FLOW
applies_to: verification
---

# CFO 参考模块覆盖矩阵 CI 与隔离验收记录

## 验收对象

- 交付：[`CFO 参考模块与页面数据覆盖矩阵`](2026-10-18--cfo-reference-module-data-coverage-v1.md)
- 提交：`d8f2ae8d617914fcd05cfd21d8484154b1411a65`
- 分支：`codex/single-machine-runtime-convergence`
- GitHub Actions：[`run 39128676851`](https://github.com/davyzhong/FLOW/actions/runs/39128676851)

## 远端 CI 结果

准确 SHA 的 workflow 启动了全部检查。除 `data-contract` 外，workflow 中其余 jobs 成功；`data-contract` 在初次运行和一次失败 job 重跑中均于约 40 分钟处被 GitHub 取消，未产生测试失败结论。第二次尝试的 job 起止时间为 `2026-10-18T13:27:19Z` 至 `2026-10-18T14:07:34Z`。未再次重跑，也未修改 CI 配置或降低覆盖。

## 隔离替代验收

为区分超时限制与实际测试结果，使用独立 Docker Compose 项目 `flow-data-contract-verify`、独立端口（PostgreSQL 25432、Redis 26379、MinIO 29000/29001）和独立数据库 `flow_contract_verify` 执行仓库原脚本 `scripts/test_data_contract.sh`。没有连接或写入常驻 `flow`、`flow_test` 或其他演示数据库。

结果：

- `tests/data_contract tests/fixtures`：133 passed，18:01
- 持久化与 Excel 数据库往返：3 passed，1:14
- Ruff：通过
- mypy：213 个源文件，无问题
- 数据契约摘要：PASS（operating=3072、financial=432、budget=120、AR=1920）

首轮隔离运行在创建数据库前启动，110 项通过、23 项因专用数据库尚未创建而在 setup 阶段报错；随后只在隔离容器内创建测试数据库并完整重跑，完整脚本成功退出。首轮结果不作为最终验收结论。

## 处置结论

工作包 7a §4.1 的矩阵内容、M1/M6 文档门禁、链接检查及隔离数据契约完整脚本均已通过。准确 SHA 的远端 `data-contract` job 因 40 分钟运行上限两次取消，不能描述为 CI 全绿；本子步据完整隔离替代验证结案，并将该 CI 限制保留为验收风险。后续如需修复 CI 时长，应作为独立 CI 治理决策处理，不改变本次数据契约验收结果。
