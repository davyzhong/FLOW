#!/usr/bin/env python3
"""S01 §2.2/§3.2 开发凭据种子：幂等补齐 role_binding 基础行。

新认证合同（S01 规格已批准）下，API 不再「未配置即放行」：
- development 模式：`FLOW_DEV_ACTOR_ID` 指向的 actor 必须有一条 active RoleBinding；
- legacy Bearer（AUTH_TOKEN）：必须有一条 active service_account RoleBinding。

本脚本按当前 DATABASE_URL 的 SQLAlchemy 方言补齐两行（均幂等）：
- pytest：conftest.py 内联同逻辑；
- 本地原型：`scripts/flow.py init` 在 SQLite 迁移后调用；
- 隔离 PostgreSQL 集成栈：CI 脚本可显式传入 job 级数据库 URL。

库不可达或 role_binding 表未迁移时打印原因并退出 0（不阻塞调用方）。
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.db import get_engine
from flow_api.security.models import RoleBinding
from flow_api.settings import get_settings

DEV_ENTERPRISE_ID = "00000000-0000-0000-0000-00000000d001"
DEV_ACTOR_DEFAULT = "flow-dev-bp"
LEGACY_ACTOR_DEFAULT = "local-dev-web"


def main(*, strict: bool = False) -> int:
    settings = get_settings()
    engine = get_engine()
    dev_actor = settings.flow_dev_actor_id or DEV_ACTOR_DEFAULT
    legacy_actor = settings.flow_legacy_actor_id or LEGACY_ACTOR_DEFAULT
    try:
        if not inspect(engine).has_table("role_binding"):
            if strict:
                raise RuntimeError("role_binding 表不存在，请先完成数据库迁移")
            print("seed_dev_principal: role_binding 表不存在（未迁移），跳过")
            return 0
        enterprise_id = UUID(DEV_ENTERPRISE_ID)
        with Session(engine) as session, session.begin():
            dev_binding = session.scalar(
                select(RoleBinding).where(
                    RoleBinding.actor_id == dev_actor,
                    RoleBinding.active.is_(True),
                )
            )
            if dev_binding is None:
                session.add(
                    RoleBinding(
                        actor_id=dev_actor,
                        role="analyst",
                        enterprise_id=enterprise_id,
                        is_service_account=False,
                        active=True,
                    )
                )
            service_account = session.scalar(
                select(RoleBinding).where(
                    RoleBinding.role == "service_account",
                    RoleBinding.active.is_(True),
                )
            )
            if service_account is None:
                session.add(
                    RoleBinding(
                        actor_id=legacy_actor,
                        role="service_account",
                        enterprise_id=enterprise_id,
                        is_service_account=True,
                        active=True,
                    )
                )
        print(f"seed_dev_principal: ok (dev_actor={dev_actor})")
        return 0
    except Exception as exc:  # noqa: BLE001 - 保持原有幂等开发种子语义
        if strict:
            raise RuntimeError("开发身份初始化失败") from exc
        print(f"seed_dev_principal: 数据库不可达，跳过（{type(exc).__name__}: {exc}）")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
