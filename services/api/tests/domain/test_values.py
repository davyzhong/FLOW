from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from flow_api.domain.enums import JobStatus, ObjectType
from flow_api.domain.ids import new_uuid7
from flow_api.domain.values import JobReceipt, Money, ObjectRef


def test_money_rejects_float_and_quantizes_half_up() -> None:
    assert Money(amount=Decimal("12.34565")).amount == Decimal("12.3457")
    assert Money(amount="-2.34565").amount == Decimal("-2.3457")

    with pytest.raises(ValidationError, match="floating-point"):
        Money(amount=12.34)


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-Infinity"])
def test_money_rejects_non_finite_amounts(amount: str) -> None:
    with pytest.raises(ValidationError, match="finite"):
        Money(amount=amount)


@pytest.mark.parametrize("currency", ["cny", "CN", "CNY1", "人民币"])
def test_money_requires_iso_style_currency(currency: str) -> None:
    with pytest.raises(ValidationError):
        Money(amount="1", currency=currency)


def test_object_ref_and_job_receipt_are_frozen_typed_contracts() -> None:
    reference = ObjectRef(
        object_type=ObjectType.FINDING,
        object_id="finding-001",
        version_id="v1",
    )
    receipt = JobReceipt(
        job_id=new_uuid7(),
        resource_id=new_uuid7(),
        status=JobStatus.QUEUED,
    )

    assert reference.object_type is ObjectType.FINDING
    assert isinstance(receipt.job_id, UUID)
    with pytest.raises(ValidationError, match="frozen"):
        reference.object_id = "changed"  # type: ignore[misc]
