
from pydantic import BaseModel

# Request
class ProcessRequest(BaseModel):
    input: str
    source : str = "api"
# Response
class ProcessResponse(BaseModel):
    tasks: list
    decisions: list
    risks: list
    summary: str