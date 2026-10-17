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
- `canonical/financial_actuals.jsonl`：24 个月 × 4 个模拟业务单元 × 24 个科目，共 2,304 行；金额单位为人民币元。损益、现金流、资产负债关键余额分别勾稽至来源登记的菜鸟 FY2022/FY2023 年报；FY2021 年末余额用于月度插值起点。公开资料没有月度或事业部明细，故这些明细按登记的确定性规则分配，属于 synthetic allocation，不是菜鸟逐月/逐事业部实际值；
- 订单数和件量是基于演示客单价派生的整数，不是菜鸟披露的实际单量；每单件数按确定性演示参数派生；
- `workbooks/damai_logistics_full_v1.xlsx`：标准工作簿（Finance BP 导入用，
  actual/budget，无 forecast——预测在 sidecar，`persistence: static-only`、
  `page_coverage: excluded`，不得冒充已上线能力）；
- `statements/damai_fy2022.yaml`、`damai_fy2023.yaml`：菜鸟申请稿披露三表
  逐行原值（IFRS，千元；来源登记血缘，非合成投影）；
- `operations/damai_segment_series.yaml`、`damai_operating_metrics.yaml`：
  DAMAI.SYN 独立分部序列与运营事实（synthetic，血缘指向 manifest.json）；
- `forecast/rolling_forecast.jsonl`：静态预测 sidecar；
- `manifest.json`：期间、行数、披露年度汇总、年度来源 fact ID、合成分配说明、逐文件 SHA-256、`synthetic: true`。

装载：`python3 scripts/seed_damai_demo.py`（幂等，经 IntakeService/领域服务链，
见规格《大麦物流演示数据设计》§4.3）。
