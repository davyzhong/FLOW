import pytest
from pydantic import SecretStr
from sqlalchemy import text

from flow_api.infrastructure.db import transaction
from flow_api.settings import get_settings


def test_required_settings_are_typed() -> None:
    settings = get_settings()

    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.redis_url.startswith("redis://")
    assert isinstance(settings.s3_access_key, SecretStr)
    assert isinstance(settings.s3_secret_key, SecretStr)


def test_postgres_transaction_is_available() -> None:
    with transaction() as session:
        assert session.scalar(text("select 1")) == 1


def test_transaction_rolls_back_on_error() -> None:
    marker = "flow_transaction_rollback_probe"

    with transaction() as session:
        session.execute(text(f"create temporary table {marker} (value integer)"))

    with pytest.raises(RuntimeError, match="force rollback"), transaction() as session:
        session.execute(text(f"insert into {marker} values (1)"))
        raise RuntimeError("force rollback")

    with transaction() as session:
        count = session.scalar(text(f"select count(*) from {marker}"))

    assert count == 0
