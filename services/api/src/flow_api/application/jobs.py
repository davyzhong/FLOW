from collections.abc import Callable
from typing import cast
from uuid import UUID

from redis import Redis

from flow_api.domain.enums import JobStatus
from flow_api.domain.ids import new_uuid7
from flow_api.domain.values import JobReceipt

JobDispatcher = Callable[[str, str], None]


class JobService:
    def __init__(self, redis_client: Redis, dispatcher: JobDispatcher) -> None:
        self._redis = redis_client
        self._dispatcher = dispatcher

    @staticmethod
    def job_key(job_type: str, resource_id: UUID, version: int) -> str:
        return f"flow:job:{job_type}:{resource_id}:{version}"

    def enqueue_once(self, job_type: str, resource_id: UUID, version: int) -> JobReceipt:
        key = self.job_key(job_type, resource_id, version)
        receipt = JobReceipt(
            job_id=new_uuid7(),
            resource_id=resource_id,
            status=JobStatus.QUEUED,
        )
        claimed = self._redis.set(key, receipt.model_dump_json(), nx=True)
        if claimed:
            try:
                self._dispatcher(job_type, str(receipt.job_id))
            except Exception:
                self._redis.delete(key)
                raise
            return receipt

        existing = self._redis.get(key)
        if existing is None:
            return self.enqueue_once(job_type, resource_id, version)
        if isinstance(existing, bytes):
            existing = existing.decode()
        return JobReceipt.model_validate_json(cast(str | bytes, existing))
