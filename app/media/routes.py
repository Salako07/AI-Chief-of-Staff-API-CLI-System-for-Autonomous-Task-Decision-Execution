"""
FastAPI routes for media processing (video/audio transcription).
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import uuid
import os
import logging
from datetime import datetime

from app.media.schemas import (
    MediaUploadResponse,
    TranscriptionJobResponse,
    TranscriptionStatusResponse,
    TranscriptionResultResponse
)
from app.media.storage import get_media_storage

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/media", tags=["media"])
storage = get_media_storage()

# Configuration
UPLOAD_DIR = os.getenv("MEDIA_UPLOAD_DIR", "/tmp/media_uploads")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_MIME_TYPES = [
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/m4a", "audio/x-m4a", "audio/mp4", "audio/ogg",
    "video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo", "video/x-matroska"
]


@router.post("/upload", response_model=MediaUploadResponse, status_code=201)
async def upload_media(
    file: UploadFile = File(..., description="Media file (audio/video)")
) -> MediaUploadResponse:
    """
    Upload a media file for transcription.

    Accepts audio and video files up to 100MB.
    Returns media_id for subsequent transcription requests.

    **Supported formats:**
    - Audio: MP3, WAV, M4A, OGG
    - Video: MP4, MOV, AVI
    """
    try:
        # Validate file type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
            )

        # Generate unique media ID
        media_id = str(uuid.uuid4())

        # Create upload directory if not exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Save file to disk
        file_path = os.path.join(UPLOAD_DIR, f"{media_id}_{file.filename}")

        # Read and validate file size
        file_content = await file.read()
        size_bytes = len(file_content)

        if size_bytes > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {size_bytes} bytes. Maximum: {MAX_FILE_SIZE} bytes"
            )

        # Write file to disk
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Persist metadata
        record = storage.create_media_file(
            media_id=media_id,
            filename=file.filename,
            file_path=file_path,
            mime_type=file.content_type,
            size_bytes=size_bytes,
            duration_seconds=None,
            status="uploaded"
        )

        logger.info(f"Media uploaded: {media_id} ({file.filename}, {size_bytes} bytes)")

        return MediaUploadResponse(
            media_id=record["id"],
            filename=record["filename"],
            size_bytes=record["size_bytes"],
            duration_seconds=record.get("duration_seconds"),
            mime_type=record["mime_type"],
            status=record["status"],
            created_at=record["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/transcribe/{media_id}", response_model=TranscriptionJobResponse, status_code=202)
async def start_transcription(
    media_id: str
) -> TranscriptionJobResponse:
    """
    Start transcription job for uploaded media file.

    Returns job_id for tracking progress.
    Transcription runs asynchronously using Celery.

    **Process:**
    1. Validates media file exists
    2. Queues Celery task for transcription
    3. Returns job_id immediately
    4. Use GET /status/{job_id} to track progress
    """
    try:
        # Fetch media record
        media_file = storage.get_media_file(media_id)
        if not media_file:
            raise HTTPException(
                status_code=404,
                detail=f"Media file not found: {media_id}"
            )

        # Prevent double processing
        if media_file["status"] == "processing":
            raise HTTPException(
                status_code=409,
                detail=f"Media file already being processed: {media_id}"
            )

        job_id = str(uuid.uuid4())
        job_record = storage.create_transcription_job(job_id=job_id, media_id=media_id, status="queued")

        # Update media status -> processing
        storage.update_media_file(media_id, status="processing")

        from app.services.media_queue import transcribe_media_task
        transcribe_media_task.delay(job_id, media_id, media_file["original_path"])

        logger.info(f"Transcription queued: job_id={job_id}, media_id={media_id}")

        return TranscriptionJobResponse(
            job_id=job_record["id"],
            media_id=job_record["media_id"],
            status=job_record["status"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start transcription: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start transcription: {str(e)}")


@router.get("/status/{job_id}", response_model=TranscriptionStatusResponse)
async def get_transcription_status(job_id: str) -> TranscriptionStatusResponse:
    """
    Get status of transcription job.

    **Statuses:**
    - `queued`: Job waiting in queue
    - `processing`: Transcription in progress
    - `completed`: Transcription complete (use GET /result/{job_id})
    - `failed`: Transcription failed (see error_message)

    **Polling:**
    Poll this endpoint every 2-5 seconds until status is `completed` or `failed`.
    """
    try:
        job = storage.get_transcription_job(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Transcription job not found: {job_id}"
            )

        transcription_text = job.get("transcription") or ""

        return TranscriptionStatusResponse(
            job_id=job["id"],
            media_id=job["media_id"],
            status=job["status"],
            progress=job.get("progress", 0),
            transcription_length=len(transcription_text) if transcription_text else None,
            processing_time_ms=job.get("processing_time_ms"),
            error_message=job.get("error_message")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/result/{job_id}", response_model=TranscriptionResultResponse)
async def get_transcription_result(job_id: str) -> TranscriptionResultResponse:
    """
    Get complete transcription result with AI processing.

    Only available when job status is `completed`.

    **Returns:**
    - Full transcription text
    - Extracted tasks, decisions, risks (from AI pipeline)
    - AI-generated summary
    - Processing time

    **Note:** This endpoint combines transcription + AI processing results.
    """
    try:
        job = storage.get_transcription_job(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Transcription job not found: {job_id}"
            )

        if job["status"] != "completed":
            raise HTTPException(
                status_code=409,
                detail=f"Transcription not yet completed. Current status: {job['status']}"
            )

        result = {
            "job_id": job["id"],
            "run_id": job.get("run_id", ""),
            "media_id": job["media_id"],
            "transcription": job.get("transcription", ""),
            "tasks": job.get("tasks", []) or [],
            "decisions": job.get("decisions", []) or [],
            "risks": job.get("risks", []) or [],
            "summary": job.get("summary", ""),
            "processing_time_ms": job.get("processing_time_ms", 0)
        }

        return TranscriptionResultResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get result: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")


@router.get("/health")
async def media_health_check():
    """Health check for media processing service."""
    return {
        "status": "healthy",
        "service": "media-processing",
        "upload_dir": UPLOAD_DIR,
        "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024),
        "active_jobs": storage.count_active_jobs()
    }
