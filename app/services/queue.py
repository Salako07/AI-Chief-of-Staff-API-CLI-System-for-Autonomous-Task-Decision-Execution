"""
Celery + Redis job queue for async execution.

WHY CELERY:
- Production-grade distributed task queue
- Automatic retry logic
- Task monitoring and management
- Horizontal scaling (multiple workers)
- Persistent queue (Redis backend)

ARCHITECTURE:
API → Celery Task Queue (Redis) → Worker Pool → Execution Engine
"""
from celery import Celery
import logging
import os

logger = logging.getLogger(__name__)

# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    "ai_chief_of_staff",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)


@celery_app.task(name="execute_actions", bind=True, max_retries=3)
def execute_actions_task(self, job_data: dict):
    """
    Celery task for executing actions asynchronously.

    Args:
        job_data: Job payload containing:
            - run_id: Processing run ID
            - output: OutputSchema dict (serialized)
            - slack_webhook_url: Optional Slack webhook

    Returns:
        dict: Execution summary
    """
    run_id = job_data.get("run_id")

    try:
        logger.info(f"[WORKER] Starting execution for run_id={run_id}")

        # Import here to avoid circular dependencies
        from app.execution.planner import ExecutionPlanner
        from app.execution.engine import ExecutionEngine, ActionExecutor
        from app.schemas.output_schema import OutputSchema
        import os

        # Reconstruct OutputSchema from dict
        output_dict = job_data.get("output")
        output = OutputSchema(**output_dict)

        slack_webhook_url = job_data.get("slack_webhook_url")

        # Initialize execution components with PostgreSQL
        # Try PostgreSQL first, fallback to SQLite
        try:
            from app.execution.idempotency_pg import PostgreSQLExecutionStore
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                execution_store = PostgreSQLExecutionStore(database_url=database_url)
                logger.info("[WORKER] Using PostgreSQL for execution store")
            else:
                raise ValueError("DATABASE_URL not set")
        except Exception as e:
            logger.warning(f"[WORKER] PostgreSQL unavailable, using SQLite fallback: {e}")
            from app.execution.idempotency import ExecutionStore
            execution_store = ExecutionStore(db_path="execution_log.db")

        execution_planner = ExecutionPlanner(
            slack_target="#ops-channel",
            alerts_target="#alerts"
        )
        action_executor = ActionExecutor(slack_webhook_url=slack_webhook_url)
        execution_engine = ExecutionEngine(
            store=execution_store,
            executor=action_executor
        )

        # Build actions from canonical state
        actions = execution_planner.build_actions(output, run_id)
        logger.info(f"[WORKER] Generated {len(actions)} actions for run_id={run_id}")

        # Execute with idempotency control
        execution_summary = execution_engine.execute_actions(actions, run_id)

        logger.info(
            f"[WORKER] Execution complete for run_id={run_id}: "
            f"{execution_summary.executed} executed, {execution_summary.skipped} skipped, "
            f"{execution_summary.failed} failed"
        )

        return {
            "run_id": run_id,
            "executed": execution_summary.executed,
            "skipped": execution_summary.skipped,
            "failed": execution_summary.failed,
            "duration_ms": execution_summary.duration_ms
        }

    except Exception as e:
        logger.error(f"[WORKER] Execution failed for run_id={run_id}: {e}")

        # Retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(f"[WORKER] Max retries exceeded for run_id={run_id}")
            return {
                "run_id": run_id,
                "error": str(e),
                "status": "failed"
            }


def enqueue_job(job_data: dict) -> str:
    """
    Enqueue job for async execution via Celery.

    Args:
        job_data: Job payload (see execute_actions_task for schema)

    Returns:
        str: Celery task ID
    """
    task = execute_actions_task.apply_async(args=[job_data])
    logger.info(f"[QUEUE] Job enqueued: run_id={job_data.get('run_id')}, task_id={task.id}")
    return task.id


def get_task_status(task_id: str) -> dict:
    """
    Get status of a Celery task.

    Args:
        task_id: Celery task ID

    Returns:
        dict: Task status info
    """
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.state,
        "result": task.result if task.ready() else None
    }
