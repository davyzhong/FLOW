---
doc_id: FLOW-GEN-DAMAI-FIXTURE-README-001
title: 大麦物流演示发行版 fixtures 说明
doc_type: generated
status: generated
version: 1.0
created_at: 2026-09-24
updated_at: 2026-09-24
owner: FLOW
generator_ref: scripts/build_damai_demo.py
input_hash: deterministic-static
---

# 大麦物流演示发行版（synthetic）

本目录由 `scripts/build_damai_demo.py` 确定性生成，**禁止手工修改**；重建命令：

    python3 scripts/build_damai_demo.py --output fixtures/damai --check

- `canonical/*.jsonl`：flow.excel.v1 canonical 数据包（批次/期间/维度/事实）；
- `workbooks/damai_logistics_full_v1.xlsx`：标准工作簿（Finance BP 导入用，
  actual/budget，无 forecast——预测在 sidecar，`persistence: static-only`、
  `page_coverage: excluded`，不得冒充已上线能力）；
- `statements/damai_fy2025.yaml`、`damai_fy2026.yaml`：闭合合成财报（六大恒等锚）；
- `forecast/rolling_forecast.jsonl`：静态预测 sidecar；
- `manifest.json`：期间、行数、核心汇总、逐文件 SHA-256、`synthetic: true`。

装载：`python3 scripts/seed_damai_demo.py`（幂等，经 IntakeService/领域服务链，
见规格《大麦物流演示数据设计》§4.3）。
