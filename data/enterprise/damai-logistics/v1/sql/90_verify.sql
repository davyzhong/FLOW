-- Read-only package checks. Set flow.enterprise_code before running.
SELECT e.code, e.name,
       (SELECT count(*) FROM enterprise_org_unit o WHERE o.enterprise_id = e.id AND o.status = 'active') AS active_org_units,
       (SELECT count(*) FROM enterprise_position p WHERE p.enterprise_id = e.id AND p.status = 'active') AS active_positions,
       (SELECT count(*) FROM enterprise_member m WHERE m.enterprise_id = e.id AND m.status = 'active') AS active_members,
       (SELECT count(*) FROM analysis_batch b JOIN analysis_cycle c ON c.id = b.analysis_cycle_id
        WHERE c.enterprise_id = e.id AND b.name = 'damai-demo-v1') AS business_batches
FROM enterprise e
WHERE e.code = current_setting('flow.enterprise_code', true);
