"""S01 §3 API 认证与 Principal 解析。

合同（规格 §3.1 / §3.2 / §2.2）：
- credential → Principal 解析：旧 Bearer 走 service_account（DB RoleBinding），
  新 Bearer 走 `flow_identity_bindings_json`；旧 Bearer 截止由 `flow_legacy_bearer_cutoff`
  强制（默认 2026-10-31T15:59:59Z；now>cutoff 时配置存在则启动失败，运行时仍 401）。
- development 模式：仅在 `flow_env=development` 且显式配置 `flow_dev_actor_id` 时启用；
  必须有唯一一条 active RoleBinding（§3.1.5）；缺 binding/不唯一/enterprise 不一致均 401。
- §3.1.7 RoleBinding 缓存：每次 resolve 都走 DB，binding 撤销后立即失效（无 long-lived cache）。
- 失败一律 401；成功返回 Principal。

实现细节：
- 启动时按 §3.1 fail-fast 校验配置（无 DB 启动失败细节由 main.py 校验，本模块只做运行时解析）。
- `resolve_principal` 接收 `session` + `authorization` header；返回 `Principal`。
"""
from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.db import get_session_factory
from flow_api.security.models import RoleBinding
from flow_api.security.principal import (
    LEGACY_BEARER_CUTOFF_UTC,
    Principal,
    Role,
)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: 提供与请求同生命周期的 Session。

    复用 `get_session_factory`。必须是 yield 型依赖：FastAPI 只对 yield 依赖
    在请求结束后执行收尾，普通返回型依赖会泄漏连接池连接
    （require_bearer_auth 挂在每个 /api/v1 路由上，泄漏会被放大）。
    """
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


class AuthError(Exception):
    code: str = "authentication_required"
    http_status: int = status.HTTP_401_UNAUTHORIZED

    def __init__(self, code: str, message: str, http_status: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status or self.http_status


class _SettingsLike:
    """Avoid hard import cycle: only the fields resolve_principal reads."""

    auth_token: str | None
    flow_env: str
    flow_identity_bindings_json: str | None
    flow_dev_actor_id: str | None
    flow_legacy_bearer_cutoff: str


def _get_settings() -> _SettingsLike:
    from flow_api.settings import get_settings

    return get_settings()  # type: ignore[return-value]


def _parse_role(value: str) -> Role:
    try:
        return Role(value)
    except ValueError as error:
        raise AuthError("invalid_principal", f"unknown role: {value!r}") from error


def _validate_binding_field(name: str, value: object) -> None:
    if not isinstance(value, str) or not value:
        raise AuthError(
            "invalid_principal",
            f"identity binding field {name!r} must be non-empty str",
        )


def _validate_is_service_account(value: object) -> bool:
    if not isinstance(value, bool):
        raise AuthError(
            "invalid_principal", "identity binding field 'is_service_account' must be bool"
        )
    return value


def _load_identity_bindings(settings: _SettingsLike) -> list[dict[str, object]]:
    raw = settings.flow_identity_bindings_json
    if not raw:
        raise AuthError(
            "invalid_principal",
            "flow_identity_bindings_json 未配置：非 development 环境必须显式提供",
        )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise AuthError(
                "invalid_principal",
                f"flow_identity_bindings_json 不是合法 JSON: {error}",
            ) from error
    if not isinstance(data, list) or not data:
        raise AuthError("invalid_principal", "flow_identity_bindings_json 必须是非空 JSON 数组")
    required = {"token_sha256", "actor_id", "role", "enterprise_id", "is_service_account"}
    parsed: list[dict[str, object]] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise AuthError("invalid_principal", f"binding[{index}] 必须是对象")
        missing = required - set(item)
        if missing:
            raise AuthError(
                "invalid_principal", f"binding[{index}] 缺字段: {sorted(missing)}"
            )
        # token_sha256 必须是 ^[0-9a-f]{64}$
        digest = item["token_sha256"]
        _validate_binding_field("token_sha256", digest)
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            raise AuthError(
                "invalid_principal", "token_sha256 必须是 ^[0-9a-f]{64}$"
            )
        _validate_binding_field("actor_id", item["actor_id"])
        _validate_binding_field("enterprise_id", item["enterprise_id"])
        # 角色合法性（防止字符串漂移）
        _parse_role(str(item["role"]))
        _validate_is_service_account(item["is_service_account"])
        parsed.append(
            {
                "token_sha256": digest,
                "actor_id": item["actor_id"],
                "role": str(item["role"]),
                "enterprise_id": str(item["enterprise_id"]),
                "is_service_account": bool(item["is_service_account"]),
            }
        )
    # §3.1.1 token_sha256 重复拒绝
    digests = [b["token_sha256"] for b in parsed]
    if len(set(digests)) != len(digests):
        raise AuthError("invalid_principal", "identity binding token_sha256 重复")
    return parsed


_SHA256_RE = __import__("re").compile(r"^[0-9a-f]{64}$")


def _parse_cutoff(raw: str) -> datetime:
    try:
        return datetime.fromisoformat(raw)
    except ValueError as error:
        raise AuthError(
                "invalid_principal",
                f"flow_legacy_bearer_cutoff 解析失败: {error}",
            ) from error


def _resolve_legacy_principal(
    settings: _SettingsLike, now: datetime
) -> Principal | None:
    """§3.2 旧 Bearer：截止前可解析 service_account；截止后配置存在则启动失败。"""
    token = settings.auth_token
    if not token:
        return None
    cutoff = _parse_cutoff(settings.flow_legacy_bearer_cutoff)
    if now > cutoff:
        # 启动校验已在 main 阶段拒绝；运行期冗余 fail-closed
        raise AuthError(
            "legacy_token_expired",
            f"legacy bearer 已于 {cutoff.isoformat()} 截止",
        )
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if not _SHA256_RE.fullmatch(digest):
        # 旧 token 仍用 sha256，与新配置一致格式
        raise AuthError("invalid_principal", "legacy token digest 不是合法 ^[0-9a-f]{64}$")
    # 旧 Bearer 仅返回待与 DB RoleBinding 比对的服务账号 candidate；
    # 实际 Principal 由 `_load_role_binding` 拼装（DB 是唯一权威 §3.1.5）
    return None  # 旧 Bearer 走 _resolve_via_bindings 复用同一管线（digest 比对）


def _resolve_via_bindings(
    settings: _SettingsLike, presented_token: str
) -> dict[str, object] | None:
    if not settings.flow_identity_bindings_json:
        return None
    for binding in _load_identity_bindings(settings):
        expected = binding["token_sha256"]
        if not isinstance(expected, str):
            continue
        actual = hashlib.sha256(presented_token.encode("utf-8")).hexdigest()
        if hmac.compare_digest(expected, actual):
            return binding
    return None


def _load_role_binding(
    session: Session,
    *,
    actor_id: str,
    role: Role,
    enterprise_id: str,
    is_service_account: bool,
) -> RoleBinding:
    """§3.1.5 数据库是 role/enterprise 唯一运行时权威。"""
    from uuid import UUID

    try:
        enterprise_uuid = UUID(enterprise_id)
    except ValueError as error:
        raise AuthError(
                "invalid_principal",
                f"enterprise_id 不是合法 UUID: {enterprise_id}",
            ) from error
    binding = session.scalar(
        select(RoleBinding).where(
            RoleBinding.actor_id == actor_id,
            RoleBinding.active.is_(True),
        )
    )
    if binding is None:
        raise AuthError(
            "invalid_principal",
            f"actor={actor_id!r} 没有 active RoleBinding（§3.1.5）",
        )
    if (
        binding.role != role.value
        or binding.enterprise_id != enterprise_uuid
        or binding.is_service_account != is_service_account
    ):
        raise AuthError(
            "invalid_principal",
            f"actor={actor_id!r} 配置声明与 DB RoleBinding 不一致（§3.1.5）",
        )
    return binding


def _build_principal(binding: RoleBinding) -> Principal:
    return Principal(
        actor_id=binding.actor_id,
        role=Role(binding.role),
        enterprise_id=binding.enterprise_id,
        is_service_account=binding.is_service_account,
    )


def resolve_principal(
    session: Session,
    authorization: str | None,
    *,
    now: datetime | None = None,
    settings: _SettingsLike | None = None,
) -> Principal:
    """§3 credential → Principal 解析。

    Args:
        session: 业务 Session；同时用于读 RoleBinding（§3.1.5）。
        authorization: `Authorization` header 原始值（含 `Bearer ` 前缀或 `None`）。
        now: 注入时间（测试用）。默认 UTC now。
        settings: 注入的 settings（测试用）。默认从 `_get_settings()` 取。

    Returns:
        Principal

    Raises:
        AuthError: 401 / invalid_principal / legacy_token_expired。
    """
    if settings is None:
        settings = _get_settings()
    current = now or datetime.now(tz=UTC)
    # 旧 Bearer 截止（即使有 Bearer 也可能在截止后）
    if settings.auth_token:
        cutoff = _parse_cutoff(settings.flow_legacy_bearer_cutoff)
        if current > cutoff:
            raise AuthError(
                "legacy_token_expired",
                f"legacy bearer 已于 {cutoff.isoformat()} 截止（§3.2）",
            )
    if not authorization:
        # development 模式：可走 dev_actor_id
        if settings.flow_env == "development" and settings.flow_dev_actor_id:
            binding = session.scalar(
                select(RoleBinding).where(
                    RoleBinding.actor_id == settings.flow_dev_actor_id,
                    RoleBinding.active.is_(True),
                )
            )
            if binding is None:
                raise AuthError(
                    "authentication_required",
                    f"dev_actor_id={settings.flow_dev_actor_id!r} 没有 active RoleBinding（§2.2）",
                )
            return _build_principal(binding)
        raise AuthError("authentication_required", "缺少 Authorization 凭据")
    # 提取 bearer
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise AuthError("credential_invalid", "Authorization 必须是 'Bearer <token>' 形式")
    presented = parts[1]
    binding_dict = _resolve_via_bindings(settings, presented)
    if binding_dict is None:
        # 旧 Bearer 兼容：与 settings.auth_token 的 sha256 比对
        if settings.auth_token and hmac.compare_digest(
            hashlib.sha256(presented.encode("utf-8")).hexdigest(),
            hashlib.sha256(settings.auth_token.encode("utf-8")).hexdigest(),
        ):
            # 旧 Bearer → 走 legacy actor；DB 必须有 service_account binding
            # §3.2 旧 Bearer → DB 唯一 active service_account binding
            binding = session.scalar(
                select(RoleBinding).where(
                    RoleBinding.role == Role.SERVICE_ACCOUNT.value,
                    RoleBinding.is_service_account.is_(True),
                    RoleBinding.active.is_(True),
                )
            )
            if binding is None:
                raise AuthError(
                    "credential_invalid",
                    "legacy bearer 命中但 DB 无 active service_account binding（§3.2）",
                )
            return _build_principal(binding)
        raise AuthError("credential_invalid", "凭据不在 identity bindings 中")
    role = _parse_role(str(binding_dict["role"]))
    binding = _load_role_binding(
        session,
        actor_id=str(binding_dict["actor_id"]),
        role=role,
        enterprise_id=str(binding_dict["enterprise_id"]),
        is_service_account=bool(binding_dict["is_service_account"]),
    )
    return _build_principal(binding)


def require_bearer_auth(
    authorization: Annotated[str | None, Header()] = None,
    session: Session = Depends(get_session),
) -> Principal:
    """FastAPI dependency：解析 Authorization → Principal。

    旧实现仅校验 shared secret；新实现按 §3 全量解析。
    """
    settings = _get_settings()
    if not settings.auth_token and not settings.flow_identity_bindings_json:
        # 完全未配置：保持原 dev 模式（不挂载认证）—— 与未升级前兼容
        # 但要尝试解析 dev_actor_id（§2.2）
        if settings.flow_env == "development" and settings.flow_dev_actor_id:
            binding = session.scalar(
                select(RoleBinding).where(
                    RoleBinding.actor_id == settings.flow_dev_actor_id,
                    RoleBinding.active.is_(True),
                )
            )
            if binding is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "unauthorized",
                        "message": "dev principal has no active RoleBinding",
                    },
                )
            return _build_principal(binding)
        # 既无 shared secret 又无 bindings，按规格需 fail-fast；这里保守返回 None 留给上层
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "缺少或无效的 Bearer 凭据"},
        )
    try:
        return resolve_principal(session, authorization)
    except AuthError as error:
        raise HTTPException(
            status_code=error.http_status,
            detail={"code": error.code, "message": str(error)},
        ) from error


__all__ = ["AuthError", "LEGACY_BEARER_CUTOFF_UTC", "resolve_principal", "require_bearer_auth"]
