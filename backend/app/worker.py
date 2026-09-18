from celery import Celery
from backend.app.core.settings import settings

celery_app = Celery(
    "ombak_nusantara_worker",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Jakarta',
    enable_utc=True,
)

celery_app.autodiscover_tasks(["backend.app.modules.planner", "backend.app.modules.social"])
