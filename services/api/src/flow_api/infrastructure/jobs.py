from celery import Celery  # type: ignore[import-untyped]
from redis import Redis

from flow_api.application.jobs import JobService
from flow_api.settings import get_settings


def create_job_service(celery_app: Celery) -> JobService:
    settings = get_settings()
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

    def dispatch(job_type: str, job_id: str) -> None:
        celery_app.send_task(
            "flow.jobs.execute",
            kwargs={"job_type": job_type, "job_id": job_id},
            task_id=job_id,
        )

    return JobService(redis_client=redis_client, dispatcher=dispatch)
