-- Read-only preflight. Set flow.enterprise_code for psql before running.
DO $$
BEGIN
    IF current_setting('flow.enterprise_code', true) IS NULL THEN
        RAISE EXCEPTION 'set flow.enterprise_code before package preflight';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM enterprise
        WHERE code = current_setting('flow.enterprise_code', true)
    ) THEN
        RAISE EXCEPTION 'target enterprise must already exist in the system';
    END IF;
    IF to_regclass('public.enterprise_org_unit') IS NULL
       OR to_regclass('public.enterprise_position') IS NULL
       OR to_regclass('public.enterprise_member') IS NULL THEN
        RAISE EXCEPTION 'enterprise directory migration is not installed';
    END IF;
END
$$;
