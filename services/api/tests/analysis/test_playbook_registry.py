import pytest

from flow_api.analysis.playbooks import PlaybookSpec, build_default_registry, build_registry


def test_default_registry_contains_five_playbooks_in_dependency_order() -> None:
    registry = build_default_registry()

    assert registry.execution_order == (
        "revenue_vpm",
        "fulfillment_cost_rve",
        "ar_cash_impact",
        "gross_profit_bridge",
        "operating_profit_bridge",
    )
    assert all(registry.specs[code].version == 1 for code in registry.execution_order)


def test_registry_rejects_duplicate_unknown_and_cyclic_dependencies() -> None:
    revenue = PlaybookSpec(code="revenue", version=1, dependencies=())
    with pytest.raises(ValueError, match="duplicate"):
        build_registry((revenue, revenue))

    with pytest.raises(ValueError, match="unknown"):
        build_registry((PlaybookSpec(code="profit", version=1, dependencies=("missing",)),))

    with pytest.raises(ValueError, match="cycle"):
        build_registry(
            (
                PlaybookSpec(code="a", version=1, dependencies=("b",)),
                PlaybookSpec(code="b", version=1, dependencies=("a",)),
            )
        )
