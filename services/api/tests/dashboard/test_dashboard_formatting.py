from decimal import Decimal

import pytest

from flow_api.dashboard.formatting import available_value, comparison_value, unavailable_value


def test_available_value_preserves_exact_decimal_scale_without_float() -> None:
    value = available_value(Decimal("136.350900"))

    assert str(value.exact_value) == "136.350900"
    assert value.display_value == "136.350900"
    assert value.semantic_direction == "neutral"

    with pytest.raises(TypeError, match="float"):
        available_value(1.25)  # type: ignore[arg-type]


def test_comparison_direction_supports_inverse_metrics() -> None:
    favorable = comparison_value("0.100000")
    unfavorable_cost = comparison_value("0.100000", inverse=True)

    assert favorable.semantic_direction == "positive"
    assert unfavorable_cost.semantic_direction == "negative"


def test_unavailable_value_has_a_typed_reason() -> None:
    value = unavailable_value(
        "comparison_not_published", "当前口径未发布该比较值"
    )

    assert value.status == "unavailable"
    assert value.exact_value is None
    assert value.display_value == "—"
