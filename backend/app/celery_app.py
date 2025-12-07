import os

from celery import Celery

from app.utils.config import config

celery_app = Celery(
    "worker",
    broker=config.get("celery_broker_url"),
    backend=config.get("celery_result_backend"),
    include=["app.celery_tasks.notebooklm"],
)

celery_app.conf.update(
    task_track_started=True,
    worker_pool="solo",  # Use solo pool for sync Playwright - no asyncio event loop
)
