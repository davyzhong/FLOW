#!/usr/bin/env python3
"""S01 §2.2/§3.2 开发凭据种子：幂等补齐 role_binding 基础行。

新认证合同（S01 规格已批准）下，API 不再「未配置即放行」：
- development 模式：`FLOW_DEV_ACTOR_ID` 指向的 actor 必须有一条 active RoleBinding；
- legacy Bearer（AUTH_TOKEN）：必须有一条 active service_account RoleBinding。

本脚本在两个环境补齐这两行（均幂等）：
- pytest / e2e：conftest.py 内联同逻辑（不经本脚本，避免子进程开销）；
- 本地/CI 真实栈：`make stack-up` 与 scripts/test_*_e2e.sh 在 alembic upgrade 后调用。

库不可达或 role_binding 表未迁移时打印原因并退出 0（不阻塞调用方）。
"""
from __future__ import annotations

import os

import psycopg

DEV_ENTERPRISE_ID = "00000000-0000-0000-0000-00000000d001"
DEV_ACTOR_DEFAULT = "flow-dev-bp"
LEGACY_ACTOR_DEFAULT = "local-dev-web"


def main() -> int:
    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        print("seed_dev_principal: DATABASE_URL 未设置，跳过")
        return 0
    url = raw.replace("postgresql+psycopg://", "postgresql://", 1)
    dev_actor = os.environ.get("FLOW_DEV_ACTOR_ID") or DEV_ACTOR_DEFAULT
    legacy_actor = os.environ.get("FLOW_LEGACY_ACTOR_ID") or LEGACY_ACTOR_DEFAULT
    try:
        with psycopg.connect(url, autocommit=True, connect_timeout=3) as conn:
            has_table = conn.execute(
                "SELECT to_regclass('public.role_binding') IS NOT NULL"
            ).fetchone()
            if not has_table or not has_table[0]:
                print("seed_dev_principal: role_binding 表不存在（未迁移），跳过")
                return 0
            conn.execute(
                """
                INSERT INTO role_binding (actor_id, role, enterprise_id,
                                          is_service_account, active)
                SELECT CAST(%s AS varchar), 'analyst', %s::uuid, false, true
                WHERE NOT EXISTS (
                    SELECT 1 FROM role_binding
                    WHERE actor_id = %s AND active IS TRUE
                )
                """,
                (dev_actor, DEV_ENTERPRISE_ID, dev_actor),
            )
            conn.execute(
                """
                INSERT INTO role_binding (actor_id, role, enterprise_id,
                                          is_service_account, active)
                SELECT %s, 'service_account', %s::uuid, true, true
                WHERE NOT EXISTS (
                    SELECT 1 FROM role_binding
                    WHERE role = 'service_account' AND active IS TRUE
                )
                """,
                (legacy_actor, DEV_ENTERPRISE_ID),
            )
        print(f"seed_dev_principal: ok (dev_actor={dev_actor})")
        return 0
    except Exception as exc:  # noqa: BLE001 - 种子失败不得阻塞调用方
        print(f"seed_dev_principal: 数据库不可达，跳过（{type(exc).__name__}: {exc}）")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
