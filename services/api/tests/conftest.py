import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_BUCKET", "flow")
os.environ.setdefault("S3_ACCESS_KEY", "flow")
os.environ.setdefault("S3_SECRET_KEY", "flow_dev_only")

# S01 §2.2 development 模式：认证边界要求 dev actor 显式配置（默认关闭会全量 401）。
# 与 scripts/seed_dev_principal.py 的默认 actor 保持一致。
os.environ.setdefault("FLOW_ENV", "development")
os.environ.setdefault("FLOW_DEV_ACTOR_ID", "flow-dev-bp")

import pytest  # noqa: E402

_DEV_BINDING_SEEDED = False


@pytest.fixture(autouse=True)
def _seed_dev_principal():
    """确保 require_bearer_auth 的 dev 路径能在 DB 中解析到 active RoleBinding。

    首次成功播种后进程内不再重复；DB 不可达或 role_binding 未迁移时静默跳过
    （unit job 无 DB、纯 domain 测试不受影响）。与 scripts/seed_dev_principal.py
    的行语义一致：flow-dev-bp/analyst + 一条 active service_account。
    """
    global _DEV_BINDING_SEEDED
    if not _DEV_BINDING_SEEDED:
        try:
            from sqlalchemy import text

            from flow_api.infrastructure.db import get_engine

            with get_engine().connect() as conn:
                has_table = conn.execute(
                    text("SELECT to_regclass('public.role_binding') IS NOT NULL")
                ).scalar()
                if has_table:
                    dev_actor = os.environ["FLOW_DEV_ACTOR_ID"]
                    conn.execute(
                        text(
                            "INSERT INTO role_binding (actor_id, role, enterprise_id,"
                            " is_service_account, active)"
                            " SELECT CAST(:actor AS varchar), 'analyst',"
                            " '00000000-0000-0000-0000-00000000d001'::uuid,"
                            " false, true"
                            " WHERE NOT EXISTS (SELECT 1 FROM role_binding"
                            " WHERE actor_id = :actor AND active IS TRUE)"
                        ),
                        {"actor": dev_actor},
                    )
                    conn.execute(
                        text(
                            "INSERT INTO role_binding (actor_id, role, enterprise_id,"
                            " is_service_account, active)"
                            " SELECT 'local-dev-web', 'service_account',"
                            " '00000000-0000-0000-0000-00000000d001'::uuid,"
                            " true, true"
                            " WHERE NOT EXISTS (SELECT 1 FROM role_binding"
                            " WHERE role = 'service_account' AND active IS TRUE)"
                        )
                    )
                    conn.commit()
                    _DEV_BINDING_SEEDED = True
        except Exception:  # noqa: BLE001 - 无 DB/未迁移环境下静默跳过
            pass
    yield
