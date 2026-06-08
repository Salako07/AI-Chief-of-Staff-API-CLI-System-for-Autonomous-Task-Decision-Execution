"""
Celery tasks for async media transcription processing.
"""
import os
import time
import logging
from datetime import datetime
from typing import Dict

# Celery imports
from app.services.queue import celery_app

# Media processing imports
from app.media.transcription import WhisperTranscriber
from app.media.processor import MediaProcessor
from app.media.storage import get_media_storage

# AI processing imports
from app.services.processor import AIChiefOfStaffProcessor
from crewai import LLM

logger = logging.getLogger(__name__)
storage = get_media_storage()


@celery_app.task(bind=True, name="app.services.media_queue.transcribe_media_task")
def transcribe_media_task(
    self,
    job_id: str,
    media_id: str,
    file_path: str,
    language: str = None
) -> Dict:
    """
    Celery task to transcribe media file and process through AI pipeline.

    This task:
    1. Downloads file from Spaces (if cloud storage) or uses local path
    2. Checks if file is video → extracts audio with FFmpeg
    3. Transcribes audio using OpenAI Whisper API
    4. Processes transcription through AI Chief of Staff pipeline
    5. Cleans up temporary files
    6. Updates job status and results

    Args:
        job_id: Transcription job ID
        media_id: Media file ID
        file_path: Path to uploaded media file OR Spaces key (if storage_type='spaces')
        language: Optional language code for transcription

    Returns:
        Dictionary with job results
    """
    start_time = time.time()
    local_video_path = None
    local_audio_path = None

    try:
        logger.info(f"[MEDIA_WORKER] Starting transcription job: {job_id} (media_id={media_id})")

        job = storage.get_transcription_job(job_id)
        if not job:
            raise Exception(f"Job not found: {job_id}")

        storage.update_transcription_job(job_id, status="processing", progress=10, started_at=datetime.utcnow())

        media_file = storage.get_media_file(media_id)
        if not media_file:
            raise Exception(f"Media file not found: {media_id}")

        storage_type = media_file.get("storage_type", "local")

        # Step 1: Download from Spaces if needed
        if storage_type == "spaces":
            logger.info(f"[MEDIA_WORKER] Downloading from Spaces: {file_path}")

            from app.media.spaces_client import get_spaces_client
            spaces_client = get_spaces_client()

            # Create temp directory for downloads
            temp_dir = os.path.join("/tmp", "media_downloads")
            os.makedirs(temp_dir, exist_ok=True)

            # Download to temp file
            local_video_path = os.path.join(temp_dir, f"{media_id}_{media_file['filename']}")
            spaces_client.download_file(
                remote_key=file_path,  # file_path is actually spaces_key
                local_path=local_video_path
            )

            logger.info(f"[MEDIA_WORKER] Download complete: {local_video_path}")
            storage.update_transcription_job(job_id, progress=20)

            # Use downloaded file for processing
            audio_file_path = local_video_path
        else:
            # Local storage - use file path directly
            local_video_path = file_path
            audio_file_path = file_path

        # Step 2: Extract audio if video file
        if media_file and media_file["mime_type"].startswith("video/"):
            logger.info(f"[MEDIA_WORKER] Video detected, extracting audio: {local_video_path}")

            processor = MediaProcessor()
            local_audio_path = processor.extract_audio(
                input_path=local_video_path,
                output_path=None,  # Auto-generate
                format="mp3",
                bitrate="192k"
            )

            logger.info(f"[MEDIA_WORKER] Audio extracted: {local_audio_path}")
            audio_file_path = local_audio_path
            storage.update_transcription_job(job_id, progress=40)

            # Cleanup video file if downloaded from Spaces
            if storage_type == "spaces" and local_video_path and os.path.exists(local_video_path):
                try:
                    os.remove(local_video_path)
                    logger.info(f"[MEDIA_WORKER] Cleaned up temp video file: {local_video_path}")
                except Exception as cleanup_err:
                    logger.warning(f"[MEDIA_WORKER] Failed to cleanup video: {cleanup_err}")
        else:
            storage.update_transcription_job(job_id, progress=30)

        # Step 2: Transcribe audio using Whisper
        logger.info(f"[MEDIA_WORKER] Transcribing audio: {audio_file_path}")

        transcriber = WhisperTranscriber()
        transcription_result = transcriber.transcribe(
            audio_file_path=audio_file_path,
            language=language
        )

        transcription_text = transcription_result["text"]
        logger.info(f"[MEDIA_WORKER] Transcription complete: {len(transcription_text)} characters")

        storage.update_transcription_job(
            job_id,
            progress=60,
            transcription=transcription_text
        )

        # Step 3: Process transcription through AI pipeline
        logger.info(f"[MEDIA_WORKER] Processing transcription through AI pipeline")

        # Initialize AI processor
        llm = LLM(model="gpt-4o-mini")
        slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        ai_processor = AIChiefOfStaffProcessor(llm=llm, tools=[], db=None, slack_webhook_url=slack_webhook)

        # Process transcription using main pipeline (returns OutputSchema)
        ai_output = ai_processor.process_input(text=transcription_text, max_retries=2)
        ai_result = ai_output.model_dump(mode="json")
        run_id = ai_result.get("metadata", {}).get("run_id")

        logger.info(f"[MEDIA_WORKER] AI processing complete: run_id={run_id}")

        storage.update_transcription_job(job_id, progress=90)

        processing_time_ms = int((time.time() - start_time) * 1000)
        storage.update_transcription_job(
            job_id,
            status="completed",
            progress=100,
            run_id=run_id,
            tasks=ai_result.get("tasks", []),
            decisions=ai_result.get("decisions", []),
            risks=ai_result.get("risks", []),
            summary=ai_result.get("summary", ""),
            processing_time_ms=processing_time_ms,
            completed_at=datetime.utcnow()
        )

        if media_file:
            storage.update_media_file(media_id, status="completed")

        # Cleanup local audio file
        if local_audio_path and os.path.exists(local_audio_path):
            try:
                os.remove(local_audio_path)
                logger.info(f"[MEDIA_WORKER] Cleaned up temp audio file: {local_audio_path}")
            except Exception as cleanup_err:
                logger.warning(f"[MEDIA_WORKER] Failed to cleanup audio: {cleanup_err}")

        logger.info(
            f"[MEDIA_WORKER] Job completed: {job_id} "
            f"({len(ai_result.get('tasks', []))} tasks, {len(ai_result.get('decisions', []))} decisions, "
            f"{len(ai_result.get('risks', []))} risks) in {processing_time_ms}ms"
        )

        return {
            "status": "completed",
            "job_id": job_id,
            "run_id": run_id,
            "transcription_length": len(transcription_text),
            "processing_time_ms": processing_time_ms
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[MEDIA_WORKER] Job failed: {job_id} - {error_msg}", exc_info=True)

        # Cleanup temp files on error
        for temp_path in [local_video_path, local_audio_path]:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"[MEDIA_WORKER] Cleaned up temp file on error: {temp_path}")
                except Exception as cleanup_err:
                    logger.warning(f"[MEDIA_WORKER] Failed to cleanup {temp_path}: {cleanup_err}")

        processing_time_ms = int((time.time() - start_time) * 1000)
        try:
            storage.update_transcription_job(
                job_id,
                status="failed",
                progress=100,
                error_message=error_msg,
                processing_time_ms=processing_time_ms,
                completed_at=datetime.utcnow()
            )
            storage.update_media_file(media_id, status="failed")
        except Exception as storage_err:
            logger.error(f"[MEDIA_WORKER] Failed to update storage for job {job_id}: {storage_err}")

        raise


@celery_app.task(name="app.services.media_queue.cleanup_old_media_files")
def cleanup_old_media_files(days_old: int = 7) -> Dict:
    """
    Celery task to clean up old media files (scheduled task).

    Deletes media files and transcription jobs older than `days_old` days.
    For Spaces-hosted files, deletes from both cloud storage and database.

    Args:
        days_old: Number of days to keep files (default: 7, configurable via SPACES_RETENTION_DAYS env var)

    Returns:
        Dictionary with cleanup statistics
    """
    try:
        # Use retention days from env var if available
        retention_days = int(os.getenv("SPACES_RETENTION_DAYS", days_old))
        logger.info(f"[MEDIA_CLEANUP] Starting cleanup of files older than {retention_days} days")

        deleted_files_local = 0
        deleted_files_spaces = 0
        deleted_jobs = 0
        spaces_errors = 0

        # Initialize Spaces client (may fail if not configured)
        try:
            from app.media.spaces_client import get_spaces_client
            spaces_client = get_spaces_client()
            spaces_available = True
        except Exception as spaces_init_err:
            logger.warning(f"[MEDIA_CLEANUP] Spaces client not available: {spaces_init_err}")
            spaces_available = False

        # Get old files before deletion
        old_files = storage.delete_old_media_files(retention_days)

        for row in old_files:
            file_path = row.get("original_path")
            media_id = row.get("id")

            # Get full media record to check storage type
            try:
                media_record = storage.get_media_file(media_id) if media_id else None
            except:
                media_record = None

            # Determine storage type
            storage_type = media_record.get("storage_type", "local") if media_record else "local"

            if storage_type == "spaces" and spaces_available:
                # Delete from Spaces
                spaces_key = media_record.get("spaces_key") if media_record else None
                if spaces_key:
                    try:
                        spaces_client.delete_file(spaces_key)
                        logger.info(f"[MEDIA_CLEANUP] Deleted from Spaces: {spaces_key}")
                        deleted_files_spaces += 1
                    except Exception as spaces_err:
                        logger.error(f"[MEDIA_CLEANUP] Failed to delete from Spaces {spaces_key}: {spaces_err}")
                        spaces_errors += 1
            else:
                # Delete from local disk
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"[MEDIA_CLEANUP] Deleted from disk: {file_path}")
                        deleted_files_local += 1
                    except OSError as fs_err:
                        logger.warning(f"[MEDIA_CLEANUP] Failed to delete {file_path}: {fs_err}")

        # Delete old transcription jobs
        deleted_jobs = len(storage.delete_old_transcription_jobs(retention_days))

        logger.info(
            f"[MEDIA_CLEANUP] Cleanup complete: {deleted_files_local} local files, "
            f"{deleted_files_spaces} Spaces files, {deleted_jobs} jobs deleted "
            f"({spaces_errors} errors)"
        )

        return {
            "status": "completed",
            "deleted_files_local": deleted_files_local,
            "deleted_files_spaces": deleted_files_spaces,
            "deleted_jobs": deleted_jobs,
            "spaces_errors": spaces_errors,
            "cutoff_days": retention_days
        }

    except Exception as e:
        logger.error(f"[MEDIA_CLEANUP] Cleanup failed: {str(e)}", exc_info=True)
        raise
