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


# ---------------------------------------------------------------------------
# 测试库隔离（G2 安全门禁）：本地运行测试时禁止直连常驻开发库 `flow`。
#
# 背景：2026-09-25 事故——本地测试默认连常驻库并清空了部分大麦演示表。
# 规则（优先级从高到低）：
#   1. `FLOW_TEST_ALLOW_PERSISTENT_DB=1` 显式豁免（后果自负，需在 issue/提交说明）；
#   2. CI 环境（GITHUB_ACTIONS=true）豁免——CI 的 flow 库是 job 级一次性容器，无事故面；
#   3. 本地默认：DATABASE_URL 指向 `flow` 库时，自动切换到独立测试库 `flow_test`
#      （按需创建，幂等），并重写环境变量——后续所有 get_settings()/engine 读到
#      的都是隔离库。DB 不可达时静默跳过（unit 测试无 DB 依赖，行为不变）。
# ---------------------------------------------------------------------------
def _switch_to_isolated_test_database() -> None:
    from urllib.parse import urlsplit

    if os.environ.get("FLOW_TEST_ALLOW_PERSISTENT_DB") == "1":
        return
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return  # CI：job 级容器库，一次性生命周期，无隔离需求

    url = os.environ["DATABASE_URL"]
    parts = urlsplit(url)
    if parts.path.lstrip("/") != "flow":
        return  # 已是其他库名（含 flow_test），视为有意配置

    admin_url = f"postgresql://{parts.netloc}/postgres"
    test_url = f"{parts.scheme}://{parts.netloc}/flow_test"
    try:
        import psycopg

        with psycopg.connect(admin_url, autocommit=True) as conn:  # noqa: S106
            exists = conn.execute(
                "SELECT 1 FROM pg_database WHERE datname = 'flow_test'"
            ).fetchone()
            if not exists:
                conn.execute("CREATE DATABASE flow_test")
    except Exception:  # noqa: BLE001 - DB 不可达：unit 测试不依赖 DB，静默跳过
        return

    os.environ["DATABASE_URL"] = test_url


_switch_to_isolated_test_database()

# S01 §2.2 development 模式：认证边界要求 dev actor 显式配置（默认关闭会全量 401）。
# 与 scripts/seed_dev_principal.py 的默认 actor 保持一致。
os.environ.setdefault("FLOW_ENV", "development")
os.environ.setdefault("FLOW_DEV_ACTOR_ID", "flow-dev-bp")

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _seed_dev_principal():
    """确保 require_bearer_auth 的 dev 路径能在 DB 中解析到 active RoleBinding。

    每个用例前幂等确保两条 binding（flow-dev-bp/analyst + 一条 active
    service_account），不做进程内缓存——tests/integration/test_migrations.py 的
    downgrade→upgrade 往返会删表重建，缓存会留下「行已没了但 flag 说种过」的坑。
    DB 不可达或表未迁移时静默跳过（unit job 无 DB、纯 domain 测试不受影响）。
    """
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
    except Exception:  # noqa: BLE001 - 无 DB/未迁移环境下静默跳过
        pass
    yield
