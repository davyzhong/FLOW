from flow_api.domain.ids import new_uuid7


def test_uuid7_values_are_time_ordered() -> None:
    first = new_uuid7()
    second = new_uuid7()

    assert first.version == 7
    assert second.version == 7
    assert second.int > first.int
