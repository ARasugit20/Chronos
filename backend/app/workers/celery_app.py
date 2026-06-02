import redis
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_ready

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "invest_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.ingest_tasks",
        "app.workers.resolver_task",
        "app.workers.retrain_task",
    ],
)

celery_app.conf.update(
    timezone="UTC",
    beat_schedule={
        "ingest-every-5-minutes": {
            "task": "app.workers.ingest_tasks.run_all_sources",
            "schedule": crontab(minute="*/5"),
        },
        "resolve-expired-recommendations": {
            "task": "app.workers.resolver_task.resolve_expired",
            "schedule": crontab(minute="0", hour="*/1"),
        },
        "weekly-retrain-stub": {
            "task": "app.workers.retrain_task.run_retrain",
            "schedule": crontab(day_of_week="monday", hour="3", minute="0"),
        },
    },
)


@worker_ready.connect
def _set_worker_heartbeat(**_: object) -> None:
    client = redis.from_url(settings.redis_url, decode_responses=True)
    client.set("worker:heartbeat", "1", ex=300)
