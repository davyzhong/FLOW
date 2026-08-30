from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from flow_api.domain.enums import JobStatus, ObjectType

MONEY_QUANTUM = Decimal("0.0001")


class Money(BaseModel):
    model_config = ConfigDict(frozen=True)

    amount: Decimal
    currency: str = Field(default="CNY", pattern=r"^[A-Z]{3}$")

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: Any) -> Decimal:
        if isinstance(value, float):
            raise ValueError("floating-point values are not accepted for money")
        try:
            amount = value if isinstance(value, Decimal) else Decimal(value)
        except (InvalidOperation, TypeError, ValueError) as error:
            raise ValueError("money amount must be decimal-compatible") from error
        if not amount.is_finite():
            raise ValueError("money amount must be finite")
        return amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


class ObjectRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    object_type: ObjectType
    object_id: str = Field(min_length=1)
    version_id: str = Field(min_length=1)


class JobReceipt(BaseModel):
    model_config = ConfigDict(frozen=True)

    job_id: UUID
    resource_id: UUID
    status: JobStatus
