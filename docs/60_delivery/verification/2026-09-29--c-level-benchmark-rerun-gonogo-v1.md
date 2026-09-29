---
doc_id: FLOW-VERIFY-C-LEVEL-GONOGO-20260929-001
title: C 级质量基准重跑与 Go/No-Go 裁决
doc_type: verification
status: draft
version: "1.0"
created_at: 2026-09-29
updated_at: 2026-09-29
owner: FLOW
commit_refs: "[3b2d130f, a28b638d, 4f997020]"
evidence_refs: "[cgo-l0-1532-of-1532, cgo-l1-1776-anchored-0-mismatch, holdout-regression-199-adapter-v5, xiaomi-24-of-25-alibaba-15-of-15, yunda-0-of-20-jdl-0-of-25, exit-conditions-3-of-6-unmet, c-level-no-go]"
applies_to: public-analysis
supersedes: []
superseded_by: null
---

# C 级质量基准重跑与 Go/No-Go 裁决（2026-09-29）

## 结论

**C 级 No-Go：六项退出条件中三项未满足（L0 未进 CI、完整独立 oracle 0/14、泛化层
holdout 未通过），两项达成（L1 准确率 100%、溯源/supersedes 可用），一项未闭环
（修复后盲评复评）。** 该结论与 2026-09-29 样本冻结审计的 No-Go 一致；本次新增
当前 HEAD 的隔离基准重跑证据（L0 1532/1532、L1 1776/1776 零差异）与 U4 关单后的
holdout 最新状态，使裁决材料从"证据不足"细化为"逐条件可对账"。

## 环境与机器结果（本次重跑）

- 代码：`main@3b2d130f51af2219`（U4 关单链 `4f997020`→`a28b638d` 之后）。
- 隔离栈：全新 Compose project `flowcgo`（宿主端口 25432/26379/29000，独立卷；
  未连接常驻 `flow`、旧 `flow_test` 或他人 `flowcverify` 栈）。
- 流程：`alembic upgrade head`（至 `0031_enterprise_directory`）→
  `seed_p5_statements.sh` 装载 5 家公司 14 份报告 → `accuracy_benchmark.py` 两级。
- **L0 入库保真：1532/1532 一致（不一致 0、缺失 0、多出 0），退出码 0。**
- **L1 页级锚验证：1776 条（strong 1022 / weak 735 / sign-flip 15 / visual 4），
  锚失效 0、值不一致 0、未入库 0，退出码 0。**
- 原始输出留存于本地 `/tmp/cgo-l0.json`、`/tmp/cgo-l1.txt`（临时证据，不入库；
  复算命令见本节"环境与机器结果"，可由任何人重复执行）。

## §3 退出条件逐项对账

| # | 条件 | 状态 | 证据 |
|---|---|---|---|
| 1 | L0 基准进 CI | ❌ 未满足 | `accuracy_benchmark.py` 未挂入任何 required job（本次核实 `.github/workflows/ci.yml` 无引用）。挂载需修改 CI 配置（用户红线），方案已备：在 data-contract job 追加 seed+L0 步骤（约 +3 分钟），待批准 |
| 2 | L1 答案集 ≥300 点、覆盖全部 14 份、oracle 独立核验通过 | ◐ 部分 | 1776 条（≥300 ✓）；L1 v5 覆盖 14 份 ✓；独立核验未通过：14 份目标报告完整逐行 oracle 为 0/14（L1 是被测答案集，不能自证），U4 车道 oracle 仅覆盖 holdout 样本 key items |
| 3 | L1 准确率 ≥100%（零容忍）且 mismatch 逐一归因 | ✅ 达成 | 本次隔离重跑 1776/1776、值不一致 0——mismatch 为空集，无需归因；含全部修订链（JDL v3、BABA FY2023 v2、行身份 v1）后仍零差异 |
| 4 | holdout 公司全流程独立复算通过 | ◐ 部分 | 回归层全绿：旧三样本 199/199（adapter-v5）、小米/阿里降级后 24/25+15/15（含勾稽一致）；**泛化层未通过**：新留出 yunda 0/20（A 股适配器版式缺口）、jdl 0/25（无适配器显式降级），首跑失败原始保留 |
| 5 | 盲评零「严重事实错误」 | ◐ 未闭环 | 2026-09-25 交叉评发现 42 确认异常，已全部归因为真实抽取错误并修复（JDL 页区间 v3、BABA FY2023 商誉减值订正、菜鸟破折号借值审定）；修复后 L1 100%。但**修复后的渲染输出未按 §3.7 Q6 rubric 重新盲评**，"零严重错误"未获独立确认 |
| 6 | supersedes 链与溯源定位在样本上可用 | ✅ 达成 | T10-B3 溯源 95.5% 行项目带页锚（迁移 0029+导入/API/前端）；B4 supersedes 链+确定性差异脚本；工作包 3a completed |

## 裁决依据

- 准确率本身（§3 条件 3）已在当前 HEAD 以隔离重跑达成 100% 零差异；No-Go 的原因
  不是数值质量，而是**独立性与泛化的证据门槛**：完整 oracle 缺位（条件 2）、泛化
  层留出失败（条件 4）、盲评复评未做（条件 5）、基准未固化为 CI 门禁（条件 1）。
- 泛化层缺口明细（U4 关单证据，holdout-results.md §5）：小米英文中报/阿里季度公告
  两版式已适配（样本已按 §4.5 降级回归）；韵达 A 股半年报（编号标题「3、合并利润
  表」+列绑定）与京东物流英文中报两版式未适配——留出身份保持，失败如实保留。

## 解锁路径（按序）

1. **L0 挂 CI**（条件 1）：一行级 CI 变更，待用户批准红线后执行；
2. **修复后盲评复评**（条件 5）：隔离渲染 14 份报告输出 → 未参与实现的 AI 按固定
   rubric 交叉评 → 零严重错误即闭环；
3. **泛化层收敛**（条件 4）：为 yunda/jdl 开发适配器（两样本按 §4.5 降级回归，从
   抽签备选池顺位补申通快递等新候选），直至出现一批未调参首跑通过的泛化证据；
   或由用户裁决接受"显式降级+边界披露"作为 C 级出口形态；
4. **完整 oracle 分批建设**（条件 2）：按报告逐份建立独立行项目 oracle（菜鸟招股书
   已被指定为回归层最难样本，可先行）。

## 与冻结审计的关系

本文档是 [样本冻结审计](2026-09-29--public-sample-freeze-oracle-audit-v1.md) 的
裁决后续：审计解决"证据是否冻结可查"，本文档解决"证据对六条件的对账与裁决"。
两者结论一致（No-Go），且均不构成对数据准确率的否定。
