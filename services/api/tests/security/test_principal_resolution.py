"""S01 §3 credential → Principal 解析的单元测试。

范围：test_principal_resolution 单元测试，注入 fake session + isolated env vars
以覆盖 §3.1/§3.2/§2.2 的解析失败与成功路径。
不连真实 DB；DB 行为在 test_security_schema.py（集成）覆盖。
"""
from __future__ import annotations

import hashlib
import json
from unittest.mock import MagicMock

import pytest

from flow_api.api.auth import (
    AuthError,
    _load_identity_bindings,
    _resolve_via_bindings,
    resolve_principal,
)
from flow_api.security.models import RoleBinding
from flow_api.security.principal import Principal, Role

# -- helpers --------------------------------------------------------------


def _sha256(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _settings_with(**overrides: object) -> MagicMock:
    s = MagicMock()
    s.auth_token = overrides.get("auth_token")
    s.flow_env = overrides.get("flow_env", "production")
    s.flow_identity_bindings_json = overrides.get("flow_identity_bindings_json")
    s.flow_dev_actor_id = overrides.get("flow_dev_actor_id")
    s.flow_legacy_bearer_cutoff = overrides.get(
        "flow_legacy_bearer_cutoff", "2099-01-01T00:00:00+00:00"
    )
    return s


def _binding_dict(
    *,
    token: str = "tok-1",
    actor_id: str = "actor-1",
    role: str = "analyst",
    enterprise_id: str = "00000000-0000-0000-0000-000000000001",
    is_service: bool = False,
) -> dict[str, object]:
    return {
        "token_sha256": _sha256(token),
        "actor_id": actor_id,
        "role": role,
        "enterprise_id": enterprise_id,
        "is_service_account": is_service,
    }


# -- §3.1 identity bindings 解析：失败路径 ----------------------------------


def test_load_identity_bindings_rejects_empty_json() -> None:
    with pytest.raises(AuthError) as exc:
        _load_identity_bindings(_settings_with(flow_identity_bindings_json=""))
    assert exc.value.code == "invalid_principal"


def test_load_identity_bindings_rejects_invalid_json() -> None:
    with pytest.raises(AuthError) as exc:
        _load_identity_bindings(_settings_with(flow_identity_bindings_json="{not json"))
    assert exc.value.code == "invalid_principal"


def test_load_identity_bindings_rejects_non_array() -> None:
    with pytest.raises(AuthError) as exc:
        _load_identity_bindings(_settings_with(flow_identity_bindings_json='{"k": 1}'))
    assert exc.value.code == "invalid_principal"


def test_load_identity_bindings_rejects_missing_field() -> None:
    raw = json.dumps(
        [{"actor_id": "a", "role": "analyst"}]
    )  # 缺 token_sha256/enterprise_id
    with pytest.raises(AuthError) as exc:
        _load_identity_bindings(_settings_with(flow_identity_bindings_json=raw))
    assert "缺字段" in str(exc.value)


def test_load_identity_bindings_rejects_bad_token_sha256_format() -> None:
    bad = _binding_dict()
    bad["token_sha256"] = "sha256:abcdef"  # 错前缀
    with pytest.raises(AuthError) as exc:
        _load_identity_bindings(
            _settings_with(flow_identity_bindings_json=json.dumps([bad]))
        )
    assert "^[0-9a-f]{64}$" in str(exc.value)


def test_load_identity_bindings_rejects_duplicate_digest() -> None:
    a = _binding_dict(token="same")
    b = _binding_dict(token="same", actor_id="b")
    with pytest.raises(AuthError) as exc:
        _load_identity_bindings(
            _settings_with(flow_identity_bindings_json=json.dumps([a, b]))
        )
    assert "重复" in str(exc.value)


def test_load_identity_bindings_rejects_unknown_role() -> None:
    bad = _binding_dict()
    bad["role"] = "super_user"
    with pytest.raises(AuthError) as exc:
        _load_identity_bindings(
            _settings_with(flow_identity_bindings_json=json.dumps([bad]))
        )
    assert "unknown role" in str(exc.value)


# -- §3.1.5 凭据比对成功路径 ----------------------------------------------


def test_resolve_via_bindings_matches_correct_token() -> None:
    s = _settings_with(flow_identity_bindings_json=json.dumps([_binding_dict(token="t1")]))
    matched = _resolve_via_bindings(s, "t1")
    assert matched is not None
    assert matched["actor_id"] == "actor-1"


def test_resolve_via_bindings_rejects_wrong_token() -> None:
    s = _settings_with(flow_identity_bindings_json=json.dumps([_binding_dict(token="t1")]))
    assert _resolve_via_bindings(s, "t2") is None


# -- §3.2 旧 Bearer 截止 --------------------------------------------------


def test_legacy_bearer_expired_raises() -> None:
    s = _settings_with(
        auth_token="old-token",
        flow_legacy_bearer_cutoff="2020-01-01T00:00:00+00:00",
    )
    session = MagicMock()
    with pytest.raises(AuthError) as exc:
        resolve_principal(session, "Bearer old-token", now=None, settings=s)
    # 现在时间 > 2020 → legacy_token_expired
    assert exc.value.code == "legacy_token_expired"


def test_legacy_bearer_within_cutoff_falls_through_to_db() -> None:
    # 旧 Bearer 截止前：仍走 DB RoleBinding（service_account）
    s = _settings_with(
        auth_token="old-token",
        flow_legacy_bearer_cutoff="2099-01-01T00:00:00+00:00",
        flow_legacy_actor_id="legacy-svc",
    )
    # session 查到 legacy binding
    binding = MagicMock(spec=RoleBinding)
    binding.actor_id = "legacy-svc"
    binding.role = Role.SERVICE_ACCOUNT.value
    binding.enterprise_id = __import__("uuid").UUID("00000000-0000-0000-0000-000000000001")
    binding.is_service_account = True
    session = MagicMock()
    session.scalar.return_value = binding
    p = resolve_principal(session, "Bearer old-token", settings=s)
    assert p.role is Role.SERVICE_ACCOUNT
    assert p.is_service_account is True


# -- §3.1.5 DB 是唯一运行时权威：缺 binding → 401 -------------------------


def test_no_matching_db_binding_raises() -> None:
    s = _settings_with(flow_identity_bindings_json=json.dumps([_binding_dict(token="t1")]))
    session = MagicMock()
    session.scalar.return_value = None  # DB 无 active binding
    with pytest.raises(AuthError) as exc:
        resolve_principal(session, "Bearer t1", settings=s)
    assert exc.value.code == "invalid_principal"


def test_db_binding_role_mismatch_raises() -> None:
    s = _settings_with(flow_identity_bindings_json=json.dumps([_binding_dict(token="t1")]))
    binding = MagicMock(spec=RoleBinding)
    binding.actor_id = "actor-1"
    binding.role = "finance_bp"  # DB role 与配置不符
    binding.enterprise_id = __import__("uuid").UUID("00000000-0000-0000-0000-000000000001")
    binding.is_service_account = False
    session = MagicMock()
    session.scalar.return_value = binding
    with pytest.raises(AuthError) as exc:
        resolve_principal(session, "Bearer t1", settings=s)
    assert "配置声明与 DB" in str(exc.value)


# -- §2.2 development 模式 + dev_actor_id ---------------------------------


def test_development_principal_with_dev_actor_id() -> None:
    s = _settings_with(
        flow_env="development",
        flow_dev_actor_id="dev-user",
        flow_identity_bindings_json=None,
        auth_token=None,
    )
    binding = MagicMock(spec=RoleBinding)
    binding.actor_id = "dev-user"
    binding.role = Role.ANALYST.value
    binding.enterprise_id = __import__("uuid").UUID("00000000-0000-0000-0000-000000000001")
    binding.is_service_account = False
    session = MagicMock()
    session.scalar.return_value = binding
    p = resolve_principal(session, None, settings=s)
    assert p.actor_id == "dev-user"
    assert p.role is Role.ANALYST


def test_development_principal_no_binding_raises() -> None:
    s = _settings_with(
        flow_env="development",
        flow_dev_actor_id="dev-user",
        flow_identity_bindings_json=None,
        auth_token=None,
    )
    session = MagicMock()
    session.scalar.return_value = None
    with pytest.raises(AuthError) as exc:
        resolve_principal(session, None, settings=s)
    assert "dev_actor_id" in str(exc.value)


def test_non_development_missing_authorization_raises() -> None:
    s = _settings_with(
        flow_env="production",
        flow_identity_bindings_json=None,
        auth_token=None,
    )
    session = MagicMock()
    with pytest.raises(AuthError) as exc:
        resolve_principal(session, None, settings=s)
    assert exc.value.code == "authentication_required"


# -- 凭据格式错误 ----------------------------------------------------------


def test_authorization_must_be_bearer_scheme() -> None:
    s = _settings_with(
        flow_identity_bindings_json=json.dumps([_binding_dict(token="t1")])
    )
    session = MagicMock()
    with pytest.raises(AuthError) as exc:
        resolve_principal(session, "Basic dXNlcjpwYXNz", settings=s)
    assert exc.value.code == "credential_invalid"


def test_authorization_must_have_token_part() -> None:
    s = _settings_with(
        flow_identity_bindings_json=json.dumps([_binding_dict(token="t1")])
    )
    session = MagicMock()
    with pytest.raises(AuthError) as exc:
        resolve_principal(session, "Bearer ", settings=s)
    assert exc.value.code == "credential_invalid"


# -- §3.1 Principal 构造成功路径 -------------------------------------------


def test_full_resolve_returns_principal_with_db_authority() -> None:
    s = _settings_with(
        flow_identity_bindings_json=json.dumps(
            [_binding_dict(token="t1", role="rule_owner", is_service=False)]
        )
    )
    enterprise_uuid = __import__("uuid").UUID("00000000-0000-0000-0000-000000000001")
    binding = MagicMock(spec=RoleBinding)
    binding.actor_id = "actor-1"
    binding.role = Role.RULE_OWNER.value
    binding.enterprise_id = enterprise_uuid
    binding.is_service_account = False
    session = MagicMock()
    session.scalar.return_value = binding
    p = resolve_principal(session, "Bearer t1", settings=s)
    assert isinstance(p, Principal)
    assert p.role is Role.RULE_OWNER
    assert p.actor_id == "actor-1"
    assert p.enterprise_id == enterprise_uuid
