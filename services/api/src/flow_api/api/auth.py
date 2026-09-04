"""API 认证边界：Bearer Token（单租户单用户起步）。

- `Settings.auth_token` 未配置 = 本机开发模式，不鉴权；
- 配置后除 health 外所有 /api/v1 路由要求 `Authorization: Bearer <token>`；
- token 比较使用 secrets.compare_digest（恒时），比较对象为完整头，
  避免按段比较泄漏前缀匹配信息。
"""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status

from flow_api.settings import get_settings


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "缺少或无效的 Bearer 凭据"},
        )
