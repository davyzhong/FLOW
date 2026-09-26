-- Transactional, tenant-scoped Damai reset. Caller sets flow.target_enterprise_id.
-- Keep system dictionaries, enterprise/cycle rows, statement history, audit events,
-- and shared stored_object rows. The Python initializer executes each statement here
-- inside the same transaction as the domain-service seed.
CREATE TEMP TABLE _damai_target_batches ON COMMIT DROP AS
SELECT b.id
FROM analysis_batch b
JOIN analysis_cycle c ON c.id = b.analysis_cycle_id
WHERE c.enterprise_id = current_setting('flow.target_enterprise_id', true)::uuid
  AND b.name = 'damai-demo-v1';
CREATE TEMP TABLE _damai_target_imports ON COMMIT DROP AS
SELECT id FROM import_version
WHERE batch_id IN (SELECT id FROM _damai_target_batches);
CREATE TEMP TABLE _damai_target_snapshots ON COMMIT DROP AS
SELECT id FROM metric_snapshot
WHERE batch_id IN (SELECT id FROM _damai_target_batches);
CREATE TEMP TABLE _damai_target_runs ON COMMIT DROP AS
SELECT id FROM analysis_run
WHERE import_version_id IN (SELECT id FROM _damai_target_imports)
   OR metric_snapshot_id IN (SELECT id FROM _damai_target_snapshots);
CREATE TEMP TABLE _damai_target_findings ON COMMIT DROP AS
SELECT id FROM finding
WHERE analysis_run_id IN (SELECT id FROM _damai_target_runs)
   OR metric_snapshot_id IN (SELECT id FROM _damai_target_snapshots);
CREATE TEMP TABLE _damai_reset_counts ON COMMIT DROP AS
SELECT
  (SELECT count(*) FROM _damai_target_batches) AS batches,
  (SELECT count(*) FROM _damai_target_imports) AS imports,
  (SELECT count(*) FROM _damai_target_snapshots) AS snapshots,
  (SELECT count(*) FROM review_event
   WHERE finding_id IN (SELECT id FROM _damai_target_findings)) AS review_events_archived,
  (SELECT count(*) FROM analysis_cycle
   WHERE enterprise_id = current_setting('flow.target_enterprise_id', true)::uuid
     AND period_key = '2026-08' AND status <> 'open') AS cycles_reopened;
INSERT INTO audit_event (
  event_type, actor_id, actor_role, enterprise_id, resource_scope, resource_type,
  resource_id, action, decision, reason_code, correlation_id, request_id,
  redacted_metadata, artifact_refs, created_at, retention_class, retain_until
)
SELECT
  'finding.review_history.archived', left(re.reviewer, 128), NULL,
  current_setting('flow.target_enterprise_id', true)::uuid, 'enterprise',
  'finding_review_event', re.finding_id::text, 'enterprise.business.reset',
  'allow', 'allow', left('enterprise-reset:' || re.id::text, 128),
  left('enterprise-reset:' || re.id::text, 128),
  jsonb_build_object(
    'source_event_id', re.id, 'finding_id', re.finding_id,
    'sequence', re.sequence, 'reviewer', re.reviewer, 'decision', re.decision,
    'comment', re.comment, 'source_created_at', re.created_at
  ), '[]'::jsonb, now(), 'security_default',
  now() + make_interval(days => current_setting('flow.audit_retention_days', true)::integer)
FROM review_event re
WHERE re.finding_id IN (SELECT id FROM _damai_target_findings);
DELETE FROM report_snapshot
WHERE metric_snapshot_id IN (SELECT id FROM _damai_target_snapshots);
DELETE FROM analysis_run
WHERE id IN (SELECT id FROM _damai_target_runs);
DELETE FROM fact_ar_collection
WHERE import_version_id IN (SELECT id FROM _damai_target_imports);
DELETE FROM fact_budget
WHERE import_version_id IN (SELECT id FROM _damai_target_imports);
DELETE FROM fact_financial_actual
WHERE import_version_id IN (SELECT id FROM _damai_target_imports);
DELETE FROM fact_operating_actual
WHERE import_version_id IN (SELECT id FROM _damai_target_imports);
DELETE FROM metric_snapshot
WHERE id IN (SELECT id FROM _damai_target_snapshots);
DELETE FROM import_version
WHERE id IN (SELECT id FROM _damai_target_imports);
DELETE FROM analysis_batch
WHERE id IN (SELECT id FROM _damai_target_batches);
UPDATE analysis_cycle SET status = 'open'
WHERE enterprise_id = current_setting('flow.target_enterprise_id', true)::uuid
  AND period_key = '2026-08' AND status <> 'open';
