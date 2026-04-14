from fastapi import APIRouter
from app.api.schema import ProcessRequest, ProcessResponse
from app.api.schema import ProcessRequest, ProcessResponse

router = APIRouter()

@router.post("/process", response_model=ProcessResponse)
async def process_input(request: ProcessRequest):
    def process (request: ProcessRequest):
        return process_handler(request)
    return process(request)