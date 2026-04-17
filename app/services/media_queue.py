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
    1. Checks if file is video → extracts audio with FFmpeg
    2. Transcribes audio using OpenAI Whisper API
    3. Processes transcription through AI Chief of Staff pipeline
    4. Updates job status and results

    Args:
        job_id: Transcription job ID
        media_id: Media file ID
        file_path: Path to uploaded media file
        language: Optional language code for transcription

    Returns:
        Dictionary with job results
    """
    start_time = time.time()

    try:
        logger.info(f"[MEDIA_WORKER] Starting transcription job: {job_id} (media_id={media_id})")

        job = storage.get_transcription_job(job_id)
        if not job:
            raise Exception(f"Job not found: {job_id}")

        storage.update_transcription_job(job_id, status="processing", progress=10, started_at=datetime.utcnow())

        media_file = storage.get_media_file(media_id)
        audio_file_path = file_path

        if media_file and media_file["mime_type"].startswith("video/"):
            logger.info(f"[MEDIA_WORKER] Video detected, extracting audio: {file_path}")

            processor = MediaProcessor()
            audio_file_path = processor.extract_audio(
                input_path=file_path,
                output_path=None,  # Auto-generate
                format="mp3",
                bitrate="192k"
            )

            logger.info(f"[MEDIA_WORKER] Audio extracted: {audio_file_path}")
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

    Args:
        days_old: Number of days to keep files (default: 7)

    Returns:
        Dictionary with cleanup statistics
    """
    try:
        logger.info(f"[MEDIA_CLEANUP] Starting cleanup of files older than {days_old} days")

        deleted_files = 0
        deleted_jobs = 0

        old_files = storage.delete_old_media_files(days_old)
        for row in old_files:
            file_path = row.get("original_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"[MEDIA_CLEANUP] Deleted file from disk: {file_path}")
                except OSError as fs_err:
                    logger.warning(f"[MEDIA_CLEANUP] Failed to delete {file_path}: {fs_err}")
            deleted_files += 1

        deleted_jobs = len(storage.delete_old_transcription_jobs(days_old))

        logger.info(
            f"[MEDIA_CLEANUP] Cleanup complete: {deleted_files} files, {deleted_jobs} jobs deleted"
        )

        return {
            "status": "completed",
            "deleted_files": deleted_files,
            "deleted_jobs": deleted_jobs,
            "cutoff_days": days_old
        }

    except Exception as e:
        logger.error(f"[MEDIA_CLEANUP] Cleanup failed: {str(e)}", exc_info=True)
        raise
