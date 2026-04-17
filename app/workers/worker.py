"""
Celery worker for background execution.

USAGE:
    celery -A app.workers.worker worker --loglevel=info

ADVANCED:
    # Multiple workers for scaling
    celery -A app.workers.worker worker --loglevel=info --concurrency=4

    # With autoscale
    celery -A app.workers.worker worker --loglevel=info --autoscale=10,3

    # Monitoring
    celery -A app.workers.worker flower  # Web UI at http://localhost:5555
"""
from app.services.queue import celery_app

# Import tasks to register them with Celery
from app.services.queue import execute_actions_task
from app.services.media_queue import transcribe_media_task, cleanup_old_media_files

if __name__ == "__main__":
    celery_app.start()
