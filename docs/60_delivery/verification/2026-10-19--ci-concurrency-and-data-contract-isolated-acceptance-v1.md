---
doc_id: FLOW-VER-CI-GATE-20261019-001
title: CI 并发治理与数据契约隔离验收
doc_type: verification
status: current
version: 1.0
created_at: 2026-10-19
updated_at: 2026-10-19
owner: FLOW
commit_refs: [dfc67283751a357d43ae23296e561cd286fea1dc]
evidence_refs: [github-actions-run-39251870852, isolated-data-contract-dfc67283, github-concurrency-cancellation]
applies_to: verification
---

# CI 并发治理与数据契约隔离验收

## 验收对象

- 代码提交：`dfc67283751a357d43ae23296e561cd286fea1dc`
- 分支：`codex/single-machine-runtime-convergence`
- GitHub Actions：[`run 39251870852`](https://github.com/davyzhong/FLOW/actions/runs/39251870852)
- 本地数据契约执行：同一代码 SHA；独立 Compose 项目 `flow-contract-dfc67283`

## CI 并发治理结果

用户批准的 workflow 顶层分组策略以工作流、PR 来源仓库和分支组成并发组，启用 `cancel-in-progress: true`。提交 `dfc67283` 推送后，前一 SHA `b2524ab4311d9c6e82c3b5ef88d6e92f42403a90` 的 run `39251317737` 自动取消，新 SHA 的 run `39251870852` 开始执行。该现象验证同分支更新不再与最新代码并行争用 CI；这不等于新 SHA 的全套 CI 全绿。

## 准确 SHA 远端门禁

`39251870852` 的 18 项作业中 17 项成功，唯一非成功项为 `data-contract`。长作业耗时：`integration` 33 分 38 秒并成功；`data-contract` 达到工作流声明的 40 分钟上限，运行 40 分 19 秒后被 GitHub 取消，日志最后只有 pytest 进度约 54% 和 `The operation was canceled`，没有测试失败报告。`publishing-golden` 用时 6 分 40 秒并成功。静态 Python 作业成功，包含 M6 文档门禁；M1 本地门禁通过。

完整 CI 结果应标记为“17/18 成功、data-contract 超时取消”，不得描述为全绿。测试被取消的根因是数据契约作业时间上限，不能靠并发策略消除；并发策略解决的是旧提交重复占用运行资源。

## 隔离替代验收

为验证超时不是测试失败，在全新 Compose 项目、独立卷和端口上运行与 CI 相同的 `scripts/test_data_contract.sh` CI 分支。隔离服务为 PostgreSQL、Redis、MinIO；宿主端口分别为 25433、26380、29002/29003，数据库和对象存储均为该项目新建。环境为 macOS 本机、Python 3.13.16；未连接常驻 `flow`、`flow_test` 或演示服务。

执行结果：

- `GITHUB_ACTIONS=true bash scripts/test_data_contract.sh`：133 项数据契约/夹具测试通过，17 分 52 秒（pytest 报告 1072.21 秒）；
- 契约摘要检查通过：operating=3072、financial=432、budget=120、ar=1920；
- 该 CI 分支不重复执行由 `integration` 覆盖的两项集成文件，也不重复执行由静态门禁覆盖的 Ruff/mypy；这些归属门禁在同一准确 SHA 上通过。

远端 40 分钟限制仍保留为风险。替代验收证明同一提交的数据契约/夹具测试范围在隔离环境成功，不把它伪称为远端 `data-contract` job 成功。

## 结案

阶段 5 按工作包的外部运行时限制处置条件结案：同分支旧 run 自动取消已验证；重复测试归属已核对；准确 SHA 上其他 17 个门禁成功；远端 `data-contract` 的测试主体在同一 SHA 的全新隔离环境 133/133 通过，摘要校验通过。明确限制为 GitHub 该 job 40 分钟上限仍不足以完成当前测试命令。后续如需拆分该 job、变更其超时或其他 workflow 行为，需先取得相应 CI 配置授权。
