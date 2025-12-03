import os

from app.utils.config import config
from celery import Celery

celery_app = Celery(
    "worker",
    broker=config.get("celery_broker_url"),
    backend=config.get("celery_result_backend"),
)

celery_app.conf.update(task_track_started=True)
