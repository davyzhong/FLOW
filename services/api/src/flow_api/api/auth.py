"""API 认证边界：Bearer Token（单租户单用户起步）。

- `Settings.auth_token` 未配置 = 本机开发模式，不鉴权；
- 配置后除 health 外所有 /api/v1 路由要求 `Authorization: Bearer <token>`；
- token 比较使用 secrets.compare_digest（恒时），比较对象为完整头，
  避免按段比较泄漏前缀匹配信息。

S01 Task 2B 新增 `resolve_principal`：把凭据解析为授权主体（Principal）。
身份只来自凭据；请求体中的 actor/operator/reviewer 字段一律不参与身份判定。
- 未配置任何凭据且 flow_env=development → DEVELOPMENT 主体（本机开发放行）；
- 命中 `principal_tokens` 登记 → 对应角色主体（含企业绑定）；
- 命中旧 `auth_token` → service_account 兼容主体（无发布/冻结/审批权），
  超过 `legacy_bearer_until` 后拒绝（401）。
"""

from __future__ import annotations

import secrets
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import Header, HTTPException, status

from flow_api.security.principal import Principal, Role
from flow_api.settings import get_settings


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "unauthorized", "message": message},
    )


def require_bearer_auth(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    token = get_settings().auth_token
    if not token:
        return  # 开发模式：未配置即不启用认证边界
    expected = f"Bearer {token}"
    if authorization is None or not secrets.compare_digest(
        authorization.encode(), expected.encode()
    ):
        raise _unauthorized("缺少或无效的 Bearer 凭据")


def resolve_principal(
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    """把 Bearer 凭据解析为授权主体；身份来源只有凭据，绝不信请求体。"""

    settings = get_settings()

    if not settings.auth_token and not settings.principal_tokens:
        if settings.flow_env == "development":
            return Principal(
                actor_id="dev-local",
                role=Role.DEVELOPMENT,
                enterprise_id=None,
                is_service_account=False,
            )
        raise _unauthorized("服务未配置任何认证凭据")  # 启动 fail-fast 之外的纵深防御

    if authorization is None or not authorization.startswith("Bearer "):
        raise _unauthorized("缺少或无效的 Bearer 凭据")
    token = authorization.removeprefix("Bearer ").encode()

    for candidate, spec in settings.principal_tokens.items():
        if secrets.compare_digest(token, candidate.encode()):
            role = Role(spec["role"])
            enterprise_raw = spec.get("enterprise_id")
            return Principal(
                actor_id=spec["actor_id"],
                role=role,
                enterprise_id=UUID(enterprise_raw) if enterprise_raw else None,
                is_service_account=role == Role.SERVICE_ACCOUNT,
            )

    if settings.auth_token and secrets.compare_digest(token, settings.auth_token.encode()):
        if settings.legacy_bearer_until is not None and date.today() > settings.legacy_bearer_until:
            raise _unauthorized("旧 Bearer 凭据已过兼容期，请使用登记的主体凭据")
        return Principal(
            actor_id="legacy-bearer",
            role=Role.SERVICE_ACCOUNT,
            enterprise_id=None,
            is_service_account=True,
        )

    raise _unauthorized("缺少或无效的 Bearer 凭据")
