---
doc_id: FLOW-PLAN-OVERNIGHT-20260924
title: 整夜全量执行计划（2026-09-24 夜班）
doc_type: plan
status: active
version: 1.0
created_at: 2026-09-24
updated_at: 2026-09-24
owner: FLOW
depends_on: [FLOW-PLAN-INTEGRATED-MASTER-20260924, FLOW-PLAN-CURRENT, FLOW-PLAN-EXECUTION-TODO]
acceptance_refs: [overnight-five-phase-completion]
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
applies_to: repository
supersedes: []
superseded_by: null
---

# 整夜全量执行计划｜2026-09-24 夜班

> 依据 [整合总计划](2026-09-24-integrated-master-plan.md) 生成，用户指令：不停顿、按序一次跑完，
> 目标"系统完全可用"。本计划按铁律先于执行落盘。
> 每个阶段有独立验收与提交点：任一阶段中断，接手者从最近一个 ✅ 后的任务继续。
> 执行分支：`codex/damai-logistics-data-audit`（本工作区）；大麦 L1 实施在独立 worktree 分支。

## 执行顺序总览

| 阶段 | 内容 | 验收 |
|---|---|---|
| P0 | 开工准备与基线核对 | 三核对完成、环境在线 |
| P1 | L3-1：10 条抽取错误修正 + 双层基准重跑 | ≥99.4%（1785/1795）且双零 |
| P2 | L2：sf_2026h1 oracle 录入 + manifest 升级 + U4 首跑 | 全行 diff 报告 + 三级归因 |
| P3 | L4：阿里 9988 分部抽取 + zto 公开数据 + 溯源链接设计 | 抽取落库/登记 + 设计文档 |
| P4 | L1：大麦线推进（视实施分支占用） | 按计划 v2.4 逐任务验收 |
| P5 | 收口：回归、文档刷新、CI、交接 | 同 SHA CI 绿 + 台账更新 |

## P0 开工准备

- [ ] P0.1 `git fetch && git status -sb && git log --oneline -5`；确认无并行会话新推进；
- [ ] P0.2 读 PROJECT_STATE 当前基线；确认 Docker daemon / 常驻栈在线（DB-backed 测试依赖）；
- [ ] P0.3 本计划文档提交推送（铁律：先沉淀后执行）。

## P1 十条抽取错误修正（2026-09-24 决策 4：AI 直修 + 订正层登记）

清单来源：[压力测试报告 §2](../60_delivery/2026-09-15-cainiao-stress-test-report.md)。

- [ ] P1.1 BABA 8 条：逐份打开 `docs/knowledge-base/02_research/original/p5_samples/alibaba_9988/BABA_FY{2020,2021,2022,2024,2025,2026}_annual_results.pdf`，
  在合并利润表定位"歸屬於非控制性權益"行（注意 FY2020 p38 提示：淨損失行实际值 2,534/2,872/4,067/6,529 系），
  抄录本期/上期真实值（含括号负数形态）；
- [ ] P1.2 JDL 2 条：`jd_logistics_2618/JDL_FY2025_annual_report.pdf` 合并现金流量表
  "存放受限制現金""已付利息"本期/上期真实值；
- [ ] P1.3 订正层登记：每条记录 原值/新值/依据（PDF 页序+印刷页码），保留审计痕迹；
- [ ] P1.4 修抽取 YAML（新版本文件，不改原件）；
- [ ] P1.5 重跑 `python3 scripts/build_answer_set_l1.py` + `python3 scripts/accuracy_benchmark.py --level L1`，
  目标：覆盖率 ≥ 99.4%（1785/1795）、锚失效 0、值不一致 0；
- [ ] P1.6 更新压力测试报告 §2 处置状态；EXECUTION_TODO 打勾；提交推送。

## P2 oracle 收尾 → U4 首跑

纪律（[oracle-register](../../validation/financial_reports/oracle-register.md) 铁律）：
只读 PDF 披露原文逐行转录；**禁止**打开抽取器输出/seed 落库值做对照；发现回填即整份作废。

- [ ] P2.1 sf_2026h1 录入：读 `sf_002352/SF_2026_H1_report.pdf`（213 页），
  key items + 主要报表行逐行转录至 `validation/financial_reports/oracle/sf_2026h1.yaml`
  （格式对齐 tencent_fy2025.yaml/zto_2026q1.yaml）；
- [ ] P2.2 oracle-register 登记：录入者=本会话、日期、页码定位、文件 SHA；
- [ ] P2.3 manifest.yaml key_items 升级为精确值（**新增精确版本条目，不改写历史行**）；
- [ ] P2.4 U4 首跑：三样本（zto_2026q1 / tencent_fy2025 / sf_2026h1）全行 diff，
  差异按三级归因（口径差异/解析误差/披露缺失）；
- [ ] P2.5 结果登记 `docs/implementation/objective-analysis/holdout-results.md`；
  更新 EXECUTION_TODO §一、ROADMAP U04 状态；提交推送。

## P3 数据扩张与溯源

- [ ] P3.1 阿里 9988 分部披露接入：六份 BABA PDF 分部注记抽取 → revenue_structure 增强
  （用户已批准 2026-09-24）；
- [ ] P3.2 zto 样本公开渠道获取（用户已授权寻找；找到后归档至 p5_samples/yto 同级目录并登记 SHA）；
- [ ] P3.3 溯源真实来源链接：先写半页设计输入（公开 URL/文件引用方案 + ProvenanceBadge/Hover 联动），
  评审后实现 statement 溯源回链；
- [ ] P3.4 每步完成即提交推送；基准受影响时重跑验证。

## P4 大麦线推进（条件触发）

- [ ] P4.1 检查 `~/.codex/worktrees/damai-logistics-implementation` 分支是否有其他会话活跃（git log 时间戳/working tree）；
- [ ] P4.2 若空闲：按计划 v2.4 执行 A0（门禁前置已在审计分支完成等效项 → 在实施分支核对 m6）→ A1 红灯合同 → 依序推进；
- [ ] P4.3 若被占用：本阶段跳过并在交接中明示，不抢分支。

## P5 收口

- [ ] P5.1 全量回归：API 定向测试 + docs m1/m6 + git diff --check；
- [ ] P5.2 文档刷新：EXECUTION_TODO 打勾（含提交哈希）、ROADMAP 状态、HANDOFF 增补本夜班批次；
- [ ] P5.3 最终提交推送 + `gh run list` 验证同 SHA CI；
- [ ] P5.4 交接总结：完成项/未完成项/风险，写入 HANDOFF。

## 停机条件（任一出现即停并记录）

- 需要改 CI/.env/迁移而规格未批准；
- oracle 录入不得不对照抽取器输出（独立性破坏）；
- 基准修正后为换绿需要弱化断言或删测试；
- Docker/对象存储不可用且无法本地替代验证——记录为"未执行"而非跳过成功。
