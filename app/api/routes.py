from fastapi import APIRouter, HTTPException
from app.api.schema import ProcessRequest, ProcessResponse
from app.api.controller import process_handler

router = APIRouter()

# Fixed: Removed fake async pattern and unnecessary nested function
@router.post("/process", response_model=ProcessResponse)
def process_input(request: ProcessRequest):
    """
    Process input text and return extracted tasks/decisions/risks.

    Execution happens asynchronously via Celery workers.
    Use /task-status/{task_id} to check execution progress.
    """
    return process_handler(request)


@router.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    """
    Get execution status for a Celery task.

    Args:
        task_id: Celery task ID returned from processing

    Returns:
        dict: Task status (PENDING, STARTED, SUCCESS, FAILURE, RETRY)
    """
    try:
        from app.services.queue import get_task_status
        return get_task_status(task_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
def health_check():
    """Health check endpoint for load balancers."""
    return {"status": "healthy", "service": "ai-chief-of-staff"}