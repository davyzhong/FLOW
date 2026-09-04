# Phase 8 Verification — Bounded AI Copilot

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 成功交互审计持久化及报告大纲批次选择已在后续修复补强。
> 当前入口见[文档导航](../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../implementation/2026-09-04-review-repairs.md)。

Date: 2026-09-02
Scope: `docs/superpowers/plans/2026-09-02-flow-v1-phase-8-copilot.md`
Design: `docs/superpowers/specs/2026-08-29-flow-v1-design.md` §12 (AI 能力与边界).

## Exit gate

`make test-copilot-evals` — runs the fixed offline evaluation suite
(`services/api/config/copilot/flow-v1-evals.yaml`, 6 cases) plus the full
copilot unit/API test package:

1. Citation completeness — every answer object cites packet-known IDs;
   unknown citations are rejected (`unknown_citation`).
2. Numeric consistency — every number in the answer must exist verbatim in
   the context packet (`uncited_number` rejections).
3. Insufficient-data degradation — empty packets yield questions-only output
   with `degradation=insufficient_data`.
4. Unapproved-findings prohibition — report outlines citing candidate or
   in-review findings are rejected (`unapproved_finding`).
5. Unverified facts cannot be stated as facts (`unverified_fact`).
6. Mapping-explanation and investigation-QA happy paths pass end-to-end with
   audit persistence.

Result: 6/6 eval cases pass; 28 copilot tests pass (providers, validator,
context builders, service, typed API).

## Governance design encoded

- `CopilotProvider` protocol with two offline implementations:
  `ScriptedProvider` (queued, replay-only) and `DeterministicProvider`
  (template answers constructed strictly from the context packet). A live
  provider adapter may implement the same protocol; live calls are opt-in
  and never gate CI.
- Context packets are allow-listed and identity-bound (batch, snapshot, run,
  metric definitions/formulas, finding, drivers, evidence) — built by the
  same Phase 7 repository used by the workbench, so no raw files, no
  cross-batch data, no canonical dumps.
- Structured answers separate `facts / judgments / hypotheses / questions`;
  facts must cite verified evidence or metric/snapshot context.
- Every interaction persists a `CopilotInteraction` audit row (migration
  `0009_copilot_interactions`): template version, provider, model, request
  references, response payload, outcome, rejection reasons, actor.
- Rejected outputs raise `copilot_validation_failed` (HTTP 422) with the
  typed reasons while still persisting the audit record.
- Browser access goes through the same-origin proxy with POST/PUT support;
  the workbench AI panel renders sections with citation badges and marks
  degraded answers explicitly.

## Evidence

| Check | Command | Result |
|---|---|---|
| Fixed eval cases | `make test-copilot-evals` | 6 passed |
| Copilot package | `uv run pytest tests/copilot -q` | 22 passed |
| Typed API | `uv run pytest tests/api/test_copilot.py -q` | 2 passed |
| Static python | `ruff check src tests && mypy src` | clean |
| Contracts | `bash scripts/generate_contracts.sh && make contracts-check` | in sync |
| Web static/unit | `pnpm -r lint && pnpm -r typecheck && pnpm --filter @flow/web test` | clean / 12 passed |
| Migration | `alembic upgrade head` (0009) | applied |
