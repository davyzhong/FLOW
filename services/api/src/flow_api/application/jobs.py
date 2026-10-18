from collections.abc import Callable
from uuid import UUID

from flow_api.domain.enums import JobStatus
from flow_api.domain.ids import new_uuid7
from flow_api.domain.values import JobReceipt

JobDispatcher = Callable[[str, str], None]


class JobService:
    """单进程同步任务分派器；流程状态由业务记录维护，不依赖外部队列。"""

    def __init__(self, dispatcher: JobDispatcher) -> None:
        self._dispatcher = dispatcher
        self._receipts: dict[tuple[str, UUID, int], JobReceipt] = {}

    @staticmethod
    def job_key(job_type: str, resource_id: UUID, version: int) -> str:
        return f"flow:job:{job_type}:{resource_id}:{version}"

    def enqueue_once(self, job_type: str, resource_id: UUID, version: int) -> JobReceipt:
        key = (job_type, resource_id, version)
        existing = self._receipts.get(key)
        if existing is not None:
            return existing
        receipt = JobReceipt(
            job_id=new_uuid7(),
            resource_id=resource_id,
            status=JobStatus.RUNNING,
        )
        self._receipts[key] = receipt
        try:
            self._dispatcher(job_type, str(receipt.job_id))
        except Exception:
            self._receipts.pop(key, None)
            raise
        completed = receipt.model_copy(update={"status": JobStatus.SUCCEEDED})
        self._receipts[key] = completed
        return completed
