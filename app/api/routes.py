from fastapi import APIRouter
from app.api.schema import ProcessRequest, ProcessResponse
from app.api.controller import process_handler

router = APIRouter()

# Fixed: Removed fake async pattern and unnecessary nested function
@router.post("/process", response_model=ProcessResponse)
def process_input(request: ProcessRequest):
    return process_handler(request)

# Health check endpoint
@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "ai-chief-of-staff"}