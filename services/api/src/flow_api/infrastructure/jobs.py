from flow_api.application.jobs import JobDispatcher, JobService


def create_job_service(dispatcher: JobDispatcher) -> JobService:
    if not callable(dispatcher):
        raise TypeError("dispatcher must be callable")
    return JobService(dispatcher=dispatcher)
