"""
Pydantic schemas for media processing.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class MediaUploadResponse(BaseModel):
    """Response after uploading a media file."""
    media_id: str = Field(..., description="Unique identifier for the media file")
    filename: str = Field(..., description="Original filename")
    size_bytes: int = Field(..., description="File size in bytes")
    duration_seconds: Optional[int] = Field(None, description="Media duration in seconds")
    mime_type: str = Field(..., description="MIME type of the file")
    status: Literal["uploaded", "processing", "completed", "failed"] = Field(default="uploaded")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TranscriptionJobResponse(BaseModel):
    """Response after starting transcription job."""
    job_id: str = Field(..., description="Unique identifier for the transcription job")
    media_id: str = Field(..., description="Media file ID being transcribed")
    status: Literal["queued", "processing", "completed", "failed"] = Field(default="queued")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


class TranscriptionStatusResponse(BaseModel):
    """Status of transcription job."""
    job_id: str
    media_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    transcription_length: Optional[int] = Field(None, description="Length of transcription text")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class TranscriptionResultResponse(BaseModel):
    """Complete transcription result with AI processing."""
    job_id: str
    run_id: str = Field(..., description="AI processing run ID")
    media_id: str
    transcription: str = Field(..., description="Full transcription text")
    tasks: list = Field(default_factory=list, description="Extracted tasks")
    decisions: list = Field(default_factory=list, description="Extracted decisions")
    risks: list = Field(default_factory=list, description="Extracted risks")
    summary: str = Field(..., description="AI-generated summary")
    processing_time_ms: int = Field(..., description="Total processing time")


class MediaFileMetadata(BaseModel):
    """Metadata extracted from media file."""
    duration_seconds: Optional[int] = None
    format: Optional[str] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
