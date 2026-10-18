---
doc_id: FLOW-VER-CFO-MODULE-CHART-ADAPTER-20261018
title: CFO 模块图表适配与追溯验收
doc_type: verification
status: current
version: 1.0
created_at: 2026-10-18
updated_at: 2026-10-18
owner: FLOW
commit_refs: [2006624c2698cabb1e2282f5b9a90d3cd919b809, 31f84fec8e2a37349dd85d1ff1a230d2dd8364b8]
evidence_refs: [cockpit-web-tests-189, cockpit-api-tests-14, web-production-build, docs-m1, workflow-39137734822]
applies_to: cockpit
---

# CFO 模块图表适配与追溯验收

## 结论

第 4 阶段子步 4.4 本轮适用范围完成。保留当前有限 API 图表合同与 ECharts 单一实现，未增加依赖，也未重算或补造业务数值。账龄、预算矩阵等需要 synthetic facts 的新视图不属于本步披露图表适配范围，必须先通过 4.5 的来源/口径校验并明确演示数据标签后再接入。

## 变更

- 单期 `bar` 标量分类系列使用已有 `buildRankBar`；多期数组继续使用组合趋势 builder。
- 两期「流动资产/非流动资产」是跨期比较，图型从不适合两桶比较的 treemap 改成柱图，原数值和期间不变。
- 标量图表缺少 periods 时，DOM 数值表使用模块当前报告期间作为列头；公式卡和瀑布图继续输出各自完整 DOM 值。
- 每个图表的指标代码可直达指标库 `?focus=` 定义；原有财报来源深链保持。
- 补齐一项领域测试 fixture，使其携带 `objective.v3` 快照合同与匹配载荷。

## 验收

- `pnpm --filter @flow/web test`：36 个测试文件、189 项通过。
- `pnpm --filter @flow/web typecheck`：通过。
- `pnpm --filter @flow/web lint`：0 errors；3 条现存 warning 位于 `action-panel.tsx`、`flow-data-table.tsx`，与本次文件无关。
- `pnpm --filter @flow/web build`：Next.js 生产构建通过，CFO 各模块路由均进入构建路由表。
- `uv run --project services/api pytest services/api/tests/api/test_cockpit_modules.py services/api/tests/cockpit/test_modules.py -q`：14 项通过。
- `uv run --project services/api ruff check ...`：相关 Python 文件通过；针对模块源文件的 mypy 通过。
- `python3 scripts/check_docs.py --phase m1`：通过。
- GitHub Actions 准确 SHA `31f84fec8e2a37349dd85d1ff1a230d2dd8364b8` 对应 run `39137734822`；记录本验收时该 workflow 仍在运行，不能表述为 CI 通过。

未运行截图采集，也未把截图作为本步验收。1440/1024/390 视口浏览器验收留在工作包 4.7。

## 限制

`CockpitModuleChart` 当前公开支持的图型是 `bar`、`line`、`ratio_bar`、`treemap`、`waterfall` 和页面公式卡。现有 `buildAgingBars`、heatmap、quadrant 等 ECharts 构建器没有适用的公开财报字段/图表合同，本步不以猜测字段或混合演示事实的方式接入。先在 4.5 复核 synthetic 发行包与真实公开事实边界，再评估独立演示层图型。
