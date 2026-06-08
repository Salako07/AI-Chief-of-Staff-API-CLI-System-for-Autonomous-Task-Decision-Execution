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
from app.media.spaces_client import get_spaces_client

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/media", tags=["media"])
storage = get_media_storage()

# Configuration
UPLOAD_DIR = os.getenv("MEDIA_UPLOAD_DIR", "/tmp/media_uploads")
# No file size limit - set to None to disable
MAX_FILE_SIZE_MB = None
MAX_FILE_SIZE = None
USE_SPACES = os.getenv("USE_SPACES_STORAGE", "true").lower() == "true"
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

    Accepts audio and video files of any size.
    Stores files in DigitalOcean Spaces (cloud) or local disk (fallback).
    Returns media_id for subsequent transcription requests.

    **Supported formats:**
    - Audio: MP3, WAV, M4A, OGG
    - Video: MP4, MOV, AVI
    """
    temp_file_path = None

    try:
        # Validate file type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
            )

        # Generate unique media ID
        media_id = str(uuid.uuid4())

        # Read file content (no size limit)
        file_content = await file.read()
        size_bytes = len(file_content)

        logger.info(f"[UPLOAD] Starting upload: {file.filename} ({size_bytes} bytes, storage={'Spaces' if USE_SPACES else 'Local'})")

        # Storage logic: Spaces (cloud) or Local (disk)
        if USE_SPACES:
            try:
                # Upload to DigitalOcean Spaces
                spaces_client = get_spaces_client()

                # Generate Spaces key: videos/YYYY/MM/media_id_filename
                now = datetime.utcnow()
                spaces_key = f"videos/{now.year}/{now.month:02d}/{media_id}_{file.filename}"

                # Create temp file for upload
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                temp_file_path = os.path.join(UPLOAD_DIR, f"{media_id}_temp_{file.filename}")

                with open(temp_file_path, "wb") as f:
                    f.write(file_content)

                # Upload to Spaces
                logger.info(f"[UPLOAD] Uploading to Spaces: {spaces_key}")
                spaces_client.upload_file(
                    local_path=temp_file_path,
                    remote_key=spaces_key,
                    acl=os.getenv("SPACES_ACL", "private"),
                    content_type=file.content_type
                )

                # Generate presigned URL (1 hour expiry for immediate preview)
                spaces_url = spaces_client.generate_presigned_url(spaces_key, expiration=3600)

                # Delete temp file after successful upload
                os.remove(temp_file_path)
                temp_file_path = None

                # Persist metadata (Spaces storage)
                record = storage.create_media_file(
                    media_id=media_id,
                    filename=file.filename,
                    file_path=spaces_key,  # Store Spaces key instead of local path
                    mime_type=file.content_type,
                    size_bytes=size_bytes,
                    duration_seconds=None,
                    status="uploaded",
                    spaces_key=spaces_key,
                    spaces_url=spaces_url,
                    storage_type="spaces"
                )

                logger.info(f"[UPLOAD] Spaces upload successful: {media_id} -> {spaces_key}")

            except Exception as spaces_err:
                logger.error(f"[UPLOAD] Spaces upload failed, falling back to local: {spaces_err}")
                # Fallback to local storage
                USE_SPACES_FALLBACK = False
                raise

        else:
            # Local disk storage (original behavior)
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            file_path = os.path.join(UPLOAD_DIR, f"{media_id}_{file.filename}")

            with open(file_path, "wb") as f:
                f.write(file_content)

            # Persist metadata (local storage)
            record = storage.create_media_file(
                media_id=media_id,
                filename=file.filename,
                file_path=file_path,
                mime_type=file.content_type,
                size_bytes=size_bytes,
                duration_seconds=None,
                status="uploaded",
                storage_type="local"
            )

            logger.info(f"[UPLOAD] Local upload successful: {media_id} -> {file_path}")

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
        logger.error(f"[UPLOAD] Upload failed: {str(e)}", exc_info=True)

        # Cleanup temp file on error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass

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


@router.get("/video/{media_id}/url")
async def get_video_url(media_id: str, expiration: int = 3600):
    """
    Generate a presigned URL for accessing a video stored in Spaces.

    Only works for videos stored in DigitalOcean Spaces (storage_type='spaces').
    For local files, returns error.

    Args:
        media_id: Media file ID
        expiration: URL expiration time in seconds (default: 1 hour, max: 7 days)

    Returns:
        dict: Presigned URL and metadata

    **Example:**
    ```
    GET /api/v1/media/video/abc-123/url?expiration=7200
    →
    {
      "media_id": "abc-123",
      "presigned_url": "https://wokka-staging.nyc3.digitaloceanspaces.com/...",
      "expires_in_seconds": 7200,
      "storage_type": "spaces"
    }
    ```
    """
    try:
        # Get media record
        media_file = storage.get_media_file(media_id)
        if not media_file:
            raise HTTPException(status_code=404, detail=f"Media file not found: {media_id}")

        storage_type = media_file.get("storage_type", "local")
        if storage_type != "spaces":
            raise HTTPException(
                status_code=400,
                detail=f"Video URL generation only supported for Spaces storage. This file uses: {storage_type}"
            )

        spaces_key = media_file.get("spaces_key")
        if not spaces_key:
            raise HTTPException(status_code=500, detail="Spaces key missing from database")

        # Validate expiration (max 7 days)
        max_expiration = 7 * 24 * 3600  # 7 days
        if expiration > max_expiration:
            expiration = max_expiration

        # Generate presigned URL
        spaces_client = get_spaces_client()
        presigned_url = spaces_client.generate_presigned_url(
            remote_key=spaces_key,
            expiration=expiration
        )

        logger.info(f"[MEDIA_API] Generated presigned URL for {media_id} (expires in {expiration}s)")

        return {
            "media_id": media_id,
            "presigned_url": presigned_url,
            "expires_in_seconds": expiration,
            "storage_type": storage_type,
            "filename": media_file["filename"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MEDIA_API] Failed to generate URL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate URL: {str(e)}")


@router.get("/video/{media_id}/metadata")
async def get_video_metadata(media_id: str):
    """
    Get detailed metadata for a video file.

    Returns information about file size, format, duration, storage location, etc.

    **Returns:**
    - File size and MIME type
    - Upload date
    - Storage type (local or Spaces)
    - Transcription status
    - Processing metadata
    """
    try:
        media_file = storage.get_media_file(media_id)
        if not media_file:
            raise HTTPException(status_code=404, detail=f"Media file not found: {media_id}")

        # Get associated transcription jobs
        from app.media.storage import get_media_storage
        storage_instance = get_media_storage()

        # Query transcription jobs for this media_id
        with storage_instance._get_cursor() as cursor:
            cursor.execute(
                "SELECT id, status, created_at, completed_at FROM transcription_jobs WHERE media_id = %s ORDER BY created_at DESC LIMIT 1",
                (media_id,)
            )
            latest_job = cursor.fetchone()
            transcription_job = dict(latest_job) if latest_job else None

        return {
            "media_id": media_file["id"],
            "filename": media_file["filename"],
            "size_bytes": media_file["size_bytes"],
            "size_mb": round(media_file["size_bytes"] / (1024 * 1024), 2),
            "mime_type": media_file["mime_type"],
            "duration_seconds": media_file.get("duration_seconds"),
            "status": media_file["status"],
            "storage_type": media_file.get("storage_type", "local"),
            "storage_location": media_file.get("spaces_key") if media_file.get("storage_type") == "spaces" else media_file["original_path"],
            "created_at": media_file["created_at"],
            "updated_at": media_file["updated_at"],
            "transcription_job": transcription_job
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MEDIA_API] Failed to get metadata: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get metadata: {str(e)}")


@router.delete("/video/{media_id}")
async def delete_video(media_id: str):
    """
    Delete a video file and associated transcription data.

    For Spaces-hosted files, deletes from both cloud storage and database.
    For local files, deletes from disk and database.
    Also cancels any pending transcription jobs.

    **Warning:** This action is permanent and cannot be undone.

    Returns:
        dict: Deletion status and statistics
    """
    try:
        media_file = storage.get_media_file(media_id)
        if not media_file:
            raise HTTPException(status_code=404, detail=f"Media file not found: {media_id}")

        storage_type = media_file.get("storage_type", "local")

        # Delete from storage (Spaces or local)
        if storage_type == "spaces":
            spaces_key = media_file.get("spaces_key")
            if spaces_key:
                try:
                    spaces_client = get_spaces_client()
                    spaces_client.delete_file(spaces_key)
                    logger.info(f"[MEDIA_API] Deleted from Spaces: {spaces_key}")
                except Exception as spaces_err:
                    logger.error(f"[MEDIA_API] Failed to delete from Spaces: {spaces_err}")
                    # Continue with database cleanup even if Spaces deletion fails
        else:
            file_path = media_file.get("original_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"[MEDIA_API] Deleted from disk: {file_path}")
                except OSError as fs_err:
                    logger.error(f"[MEDIA_API] Failed to delete from disk: {fs_err}")

        # Delete transcription jobs (CASCADE will handle this, but let's be explicit)
        from app.media.storage import get_media_storage
        storage_instance = get_media_storage()

        with storage_instance._get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM transcription_jobs WHERE media_id = %s RETURNING id",
                (media_id,)
            )
            deleted_jobs = cursor.fetchall()
            deleted_job_count = len(deleted_jobs)

        # Delete media file record
        storage.delete_media_file(media_id)

        logger.info(f"[MEDIA_API] Deleted media file: {media_id} ({deleted_job_count} jobs)")

        return {
            "status": "deleted",
            "media_id": media_id,
            "storage_type": storage_type,
            "deleted_jobs": deleted_job_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MEDIA_API] Failed to delete media: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete media: {str(e)}")


@router.get("/health")
async def media_health_check():
    """Health check for media processing service."""
    return {
        "status": "healthy",
        "service": "media-processing",
        "upload_dir": UPLOAD_DIR,
        "max_file_size_mb": "unlimited",
        "storage_backend": "spaces" if USE_SPACES else "local",
        "active_jobs": storage.count_active_jobs()
    }
