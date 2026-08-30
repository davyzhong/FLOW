from uuid import uuid4

from redis import Redis

from flow_api.application.jobs import JobService
from flow_api.settings import get_settings


def test_same_job_key_is_enqueued_once() -> None:
    settings = get_settings()
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    resource_id = uuid4()
    dispatched: list[tuple[str, str]] = []
    service = JobService(
        redis_client=redis_client,
        dispatcher=lambda job_type, job_id: dispatched.append((job_type, job_id)),
    )

    first = service.enqueue_once("import", resource_id, 1)
    second = service.enqueue_once("import", resource_id, 1)

    assert first.job_id == second.job_id
    assert first.resource_id == resource_id
    assert len(dispatched) == 1

    redis_client.delete(service.job_key("import", resource_id, 1))
