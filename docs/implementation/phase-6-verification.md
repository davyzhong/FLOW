# Phase 6 Verification — Governed Finance BP Dashboard

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。
> 当前入口见[文档导航](../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../implementation/2026-09-04-review-repairs.md)。

Date: 2026-09-02
Design: `docs/superpowers/specs/2026-08-29-flow-v1-design.md` §9
Fidelity record: `docs/implementation/phase-6-dashboard-fidelity.md`

## Exit gate

`make test-dashboard` starts a fresh governed demo publication, a FastAPI
process and a Next.js process on dynamically allocated loopback ports, then
runs only the seven Phase 6 browser checks:

1. the browser consumes only `/api/v1/dashboard/overview` and never reads raw,
   canonical, Metric Value, Analysis Run or Finding persistence endpoints;
2. stale and degraded states remain explicit;
3. a failed request can be retried;
4. 1440×900 and 1920×1080 visual baselines remain within the approved pixel
   tolerance;
5. the real governed page supports Month/YTD filters and preserves immutable
   batch, metric-snapshot, analysis-run and finding identity in the
   Investigation handoff;
6. the rendered dashboard has no serious or critical axe violations.

Current local result: **7/7 passed in 13.8 seconds**. The readiness summary
confirmed `state=ready`, 8 metric cards, 12 trend months, 4 ranked findings and
8 product rows.

## Evidence

| Check | Command | Result |
|---|---|---|
| Dashboard model/API/integration coverage | `make test-dashboard` bootstrap and API readiness probe | ready, identity-bound governed projection |
| Browser network boundary | `dashboard-network.spec.ts` | passed |
| Explicit failure/degradation states | `dashboard-states.spec.ts` | 2 passed |
| Visual fidelity | `dashboard-visual.spec.ts` | 2 passed at 1440 and 1920 |
| Filter and Investigation handoff | `dashboard.spec.ts` | passed |
| Accessibility | `dashboard.spec.ts` axe check | passed |
| Deterministic visual baselines | `apps/web/e2e/__snapshots__/dashboard-*-{darwin,linux}.png` | present for both supported CI/local platforms |

## Baseline reliability repairs

The 2026-09-02 re-verification exposed three local repeatability defects that
had been hidden by a clean CI runner:

- fixed API/Web ports collided with long-lived developer processes; both
  Dashboard and Investigation gates now allocate unused loopback ports;
- the TCP-only startup probe could reach Next.js before its first API proxy
  route compilation completed; the governed HTTP readiness probe now has a
  bounded 60-second first-request budget;
- the Next.js proxy forwarded the upstream `Response.body` stream directly.
  React development-mode request cancellation could strand that stream and
  make later Playwright requests take 60 seconds or more. The proxy now buffers
  the small JSON response before returning it, with a unit test proving the
  downstream response owns a distinct body stream.

The Playwright assertion budget remains 15 seconds. The passing gate therefore
does not depend on relaxing the observed failure beyond the product's current
local acceptance threshold.

## Governance boundary

- Browser components render typed API values and do not recompute finance
  metrics, drivers or finding rankings.
- The dashboard reads only published imports, metric snapshots and analysis
  runs.
- Missing, partial, degraded and stale data remain visible rather than being
  silently replaced by front-end fixtures.
- Dimension filters are limited to combinations supported by the governed
  metric grain; filtered pages do not re-rank global findings.

## Carry-forward

Phase 7 continues from the immutable Investigation handoff. Phase 9 publishing
uses approved findings from that same governed object graph. Dashboard response
performance on materially larger real pilot datasets remains a pilot
measurement, not a Phase 6 completion claim.
