from celery import Celery  # type: ignore[import-untyped]

from flow_api.settings import get_settings

settings = get_settings()
celery_app = Celery("flow", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])


@celery_app.task(name="flow.jobs.execute")  # type: ignore[untyped-decorator]
def execute_job(job_type: str, job_id: str) -> dict[str, str]:
    return {"job_type": job_type, "job_id": job_id, "status": "accepted"}
