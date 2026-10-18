from uuid import uuid4

from flow_api.application.jobs import JobService


def test_same_job_key_is_enqueued_once() -> None:
    resource_id = uuid4()
    dispatched: list[tuple[str, str]] = []
    service = JobService(
        dispatcher=lambda job_type, job_id: dispatched.append((job_type, job_id)),
    )

    first = service.enqueue_once("import", resource_id, 1)
    second = service.enqueue_once("import", resource_id, 1)

    assert first.job_id == second.job_id
    assert first.resource_id == resource_id
    assert first.status.value == "succeeded"
    assert len(dispatched) == 1
