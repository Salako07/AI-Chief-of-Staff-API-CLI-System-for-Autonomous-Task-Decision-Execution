
from pydantic import BaseModel
from typing import List
from app.schemas.output_schema import Task, Decision, Risk

# Request
class ProcessRequest(BaseModel):
    text: str  # Fixed: Changed from 'input' to 'text' to match controller usage
    source: str = "api"

# Response
class ProcessResponse(BaseModel):
    run_id: str
    tasks: List[Task]  # Fixed: Properly typed instead of generic list
    decisions: List[Decision]
    risks: List[Risk]
    summary: str