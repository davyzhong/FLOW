# Phase 9 Verification — Unified Publishing

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 文末待补的报告 API/下载已在 Pilot Phase 1 落地；冻结内容持久化、存储对象与 PPT 正文等后续修复以最新验收为准。PDF 魔数/体积检查不等于逐项提取 PDF 文本验证。
> 当前入口见[文档导航](../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../implementation/2026-09-04-review-repairs.md)。

Date: 2026-09-02
Scope: `docs/superpowers/plans/2026-09-02-flow-v1-phase-9-publishing.md`
Design: `docs/superpowers/specs/2026-08-29-flow-v1-design.md` §13.

## Exit gate

`make test-publishing-golden` — one command runs the full governed pipeline
on a fresh demo batch and proves cross-format consistency:

1. Publish demo import → metric snapshot → analysis run (all idempotent,
   published, identity-bound).
2. Approve the top finding through the Phase 7 state machine (conclusion
   complete, all evidence verified).
3. Freeze the Report Snapshot (versioned per metric snapshot).
4. Render PPTX / XLSX / HTML from the frozen view.
5. Print the frozen HTML to PDF through pinned Chromium
   (`npx playwright pdf`).
6. Extract canonical key values (report version, batch/snapshot/run ids,
   every metric current value, approved finding impacts) from each artifact
   and verify identity across pptx/xlsx/html; verify PDF magic bytes and
   non-trivial size.

Result: passed — all four formats carry identical key values and versions.

## Evidence

| Check | Command | Result |
|---|---|---|
| Freeze + renderers + attempts | `uv run pytest tests/publishing -q` | 3 passed |
| Golden gate | `make test-publishing-golden` | passed |
| Static python | `ruff check src tests && mypy src` | clean |
| Contracts | regenerated (`publishing` API) | in sync |

## Design decisions encoded

- Renderers are pure functions over the frozen `ReportView`; they never
  recompute money. Metric `actual_month`/`budget_month` exact decimal
  strings and approved finding impacts are copied verbatim into every
  format; each artifact carries the identity footer (batch, snapshot, run,
  report version, engine versions, generation time).
- `PublicationService` records every attempt (queued→running→succeeded/
  failed) with the stored object; a failed PDF printer retries without
  rebuilding the snapshot. Storage is injectable for fast network-free
  tests.
- PDF printing is deliberately layered out of the Python process: the gate
  prints the frozen HTML with the repository's pinned Chromium, keeping the
  API image free of browser dependencies.

## Carry-forward

- `make acceptance` (Phase 10) chains this gate with all previous gates.
- Report Snapshot API exposure to Finance BP (download endpoints) is a
  fast-follow on top of the persisted publication attempts.
