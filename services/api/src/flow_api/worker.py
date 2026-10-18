"""兼容旧 CI Compose 栈的测试 Worker，不参与单机产品运行。"""

import os

from celery import Celery  # type: ignore[import-untyped]

celery_app = Celery(
    "flow-test",
    broker=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
)
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])


@celery_app.task(name="flow.jobs.execute")  # type: ignore[untyped-decorator]
def execute_job(job_type: str, job_id: str) -> dict[str, str]:
    """旧健康检查任务桩；业务任务由 API 同步执行。"""
    return {"job_type": job_type, "job_id": job_id, "status": "accepted"}
