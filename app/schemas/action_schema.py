"""
Action and Execution schemas for the execution layer.

These schemas define the contract for action routing, idempotency, and execution tracking.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
from datetime import datetime, timezone
import uuid


class Action(BaseModel):
    """
    Represents an action to be executed by the system.

    Actions are deterministically generated from canonical state and must be idempotent.
    """
    id: str = Field(..., description="Deterministic action ID (hash-based)")
    type: Literal["slack", "email", "notion", "webhook"] = Field(..., description="Action type")
    title: str = Field(..., description="Human-readable action description")
    payload: Dict[str, Any] = Field(..., description="Action-specific data")
    target: str = Field(..., description="Target destination (channel, email, page ID, URL)")
    status: Literal["pending", "executed", "failed", "skipped"] = Field(default="pending")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "task-schedule-meeting-abc123",
                "type": "slack",
                "title": "Task Assigned: Schedule meeting with Sarah",
                "payload": {"title": "Schedule meeting", "owner": "John"},
                "target": "#ops-channel",
                "status": "pending"
            }
        }


class ExecutionResult(BaseModel):
    """
    Result of executing a single action.
    """
    action_id: str
    action_type: str
    success: bool
    status: Literal["executed", "failed", "skipped"]
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None


class ExecutionLog(BaseModel):
    """
    Permanent log entry for executed actions (stored in DB).
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_id: str = Field(..., description="Deterministic action ID")
    action_hash: str = Field(..., description="SHA-256 hash of action payload")
    action_type: str
    status: Literal["executed", "failed", "skipped"]
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None
    run_id: str = Field(..., description="Processing run ID for traceability")

    class Config:
        json_schema_extra = {
            "example": {
                "action_id": "task-schedule-meeting-abc123",
                "action_hash": "a3f5b2c...",
                "action_type": "slack",
                "status": "executed",
                "run_id": "bd6b10bb-0605-4317-a302-6a2f3c1f7719"
            }
        }


class ExecutionSummary(BaseModel):
    """
    Summary of all executions for a processing run.
    """
    run_id: str
    total_actions: int
    executed: int
    skipped: int
    failed: int
    duration_ms: int
    results: list[ExecutionResult]
