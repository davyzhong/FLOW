from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from sqlalchemy import JSON, BigInteger, Numeric, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator, TypeEngine

# 模型使用可跨 SQLite/PostgreSQL 编译的类型；PostgreSQL 保留原生 JSONB/UUID。
JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")
UUID_TYPE = Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql")


def json_type(*, none_as_null: bool = False) -> JSON:
    return JSON(none_as_null=none_as_null).with_variant(
        JSONB(none_as_null=none_as_null), "postgresql"
    )


class ExactNumeric(TypeDecorator[Decimal]):
    """PostgreSQL NUMERIC; SQLite scaled integer with Decimal conversion."""

    impl = Numeric
    cache_ok = True

    def __init__(self, precision: int, scale: int) -> None:
        self.precision = precision
        self.scale = scale
        super().__init__(precision=precision, scale=scale)

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(BigInteger())
        return dialect.type_descriptor(Numeric(self.precision, self.scale))

    def process_bind_param(
        self, value: Decimal | int | float | str | None, dialect: Dialect
    ) -> int | Decimal | None:
        if value is None:
            return None
        try:
            decimal_value = Decimal(str(value)).quantize(
                Decimal(1).scaleb(-self.scale), rounding=ROUND_HALF_UP
            )
        except InvalidOperation as error:
            raise ValueError(
                f"value does not fit NUMERIC({self.precision},{self.scale})"
            ) from error
        if abs(decimal_value) >= Decimal(10) ** (self.precision - self.scale):
            raise ValueError(f"value does not fit NUMERIC({self.precision},{self.scale})")
        if dialect.name == "sqlite":
            scaled = int(decimal_value.scaleb(self.scale))
            if not -(2**63) <= scaled < 2**63:
                raise OverflowError("SQLite exact numeric exceeds signed 64-bit storage")
            return scaled
        return decimal_value

    def process_result_value(
        self, value: Decimal | int | float | str | None, dialect: Dialect
    ) -> Decimal | None:
        if value is None:
            return None
        if dialect.name == "sqlite":
            return Decimal(int(value)).scaleb(-self.scale)
        return Decimal(str(value))


class Base(DeclarativeBase):
    pass
