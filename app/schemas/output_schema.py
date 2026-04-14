from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Task(BaseModel):
    id: Optional[str] = Field(default=None, description="Unique task ID")
    title: str = Field(..., description="Clear, concise task description")
    owner: Optional[str] = Field(default=None, description="Person responsible for the task")
    deadline: Optional[str] = Field(default=None, description="Deadline in natural language or ISO format")
    priority: Optional[str] = Field(default="medium", description="low, medium, high")
    status: Optional[str] = Field(default="pending", description="pending, in_progress, completed")


class Decision(BaseModel):
    id: Optional[str] = None
    decision: str = Field(..., description="Decision that has been made")
    made_by: Optional[str] = None
    timestamp: Optional[datetime] = None


class Risk(BaseModel):
    id: Optional[str] = None
    risk: str = Field(..., description="Identified risk or blocker")
    severity: Optional[str] = Field(default="medium", description="low, medium, high")
    mitigation: Optional[str] = Field(default=None, description="Suggested mitigation strategy")


class AgentMetadata(BaseModel):
    source: Optional[str] = Field(default="cli", description="cli, api, email, etc.")
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    run_id: Optional[str] = Field(default=None, description="Unique execution ID")


class OutputSchema(BaseModel):
    tasks: List[Task] = Field(default_factory=list)
    decisions: List[Decision] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    summary: str = Field(..., description="Human-readable summary of the input")
    metadata: AgentMetadata