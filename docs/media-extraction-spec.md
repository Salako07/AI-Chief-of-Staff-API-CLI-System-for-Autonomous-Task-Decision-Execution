# Media Extraction Service Specification

## Overview
Add video/audio transcription capabilities to AI Chief of Staff system.

## Architecture

### 1. Technology Stack
- **Transcription:** OpenAI Whisper API (gpt-4o-audio-preview)
- **Media Processing:** FFmpeg (extract audio from video)
- **Storage:** Temporary local storage + optional S3
- **Queue:** Existing Celery + Redis
- **Database:** Existing PostgreSQL

### 2. API Endpoints

#### POST /api/v1/media/upload
Upload media file for processing.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/media/upload \
  -F "file=@meeting.mp4" \
  -F "process_immediately=true"
```

**Response:**
```json
{
  "media_id": "uuid-here",
  "filename": "meeting.mp4",
  "size_bytes": 15728640,
  "duration_seconds": 180,
  "status": "uploaded",
  "created_at": "2026-04-17T13:30:00Z"
}
```

#### POST /api/v1/media/transcribe/{media_id}
Start transcription process.

**Response:**
```json
{
  "job_id": "uuid-here",
  "media_id": "uuid-here",
  "status": "processing",
  "estimated_completion": "2026-04-17T13:35:00Z"
}
```

#### GET /api/v1/media/status/{job_id}
Check transcription status.

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "progress": 100,
  "transcription_length": 1500,
  "processing_time_ms": 45000
}
```

#### GET /api/v1/media/result/{job_id}
Get processed results.

**Response:**
```json
{
  "job_id": "uuid-here",
  "run_id": "uuid-here",
  "transcription": "Full transcript text...",
  "tasks": [...],
  "decisions": [...],
  "risks": [...],
  "summary": "..."
}
```

### 3. Database Schema

```sql
CREATE TABLE media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_path VARCHAR(500),
    mime_type VARCHAR(100),
    size_bytes BIGINT,
    duration_seconds INTEGER,
    status VARCHAR(50), -- uploaded, processing, completed, failed
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE transcription_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    media_id UUID REFERENCES media_files(id),
    run_id UUID, -- links to AI pipeline run
    transcription TEXT,
    status VARCHAR(50),
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    processing_time_ms INTEGER
);
```

### 4. File Structure

```
app/
├── media/
│   ├── __init__.py
│   ├── routes.py          # FastAPI endpoints
│   ├── transcription.py   # Whisper API integration
│   ├── processor.py       # Media file handling (FFmpeg)
│   ├── storage.py         # File storage management
│   └── schemas.py         # Pydantic models
├── services/
│   └── media_queue.py     # Celery tasks for async processing
```

### 5. Implementation Steps

#### Step 1: Install Dependencies
```bash
pip install openai-whisper ffmpeg-python python-multipart
```

#### Step 2: Create Media Routes
```python
# app/media/routes.py
from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/api/v1/media", tags=["media"])

@router.post("/upload")
async def upload_media(file: UploadFile = File(...)):
    # Save file temporarily
    # Extract metadata (duration, size)
    # Store in database
    # Return media_id
    pass

@router.post("/transcribe/{media_id}")
async def transcribe_media(media_id: str):
    # Queue Celery task
    # Return job_id
    pass
```

#### Step 3: Whisper Integration
```python
# app/media/transcription.py
import openai

def transcribe_audio(file_path: str) -> str:
    """Transcribe audio using OpenAI Whisper."""
    with open(file_path, "rb") as audio:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            language="en"
        )
    return transcript.text
```

#### Step 4: Celery Task
```python
# app/services/media_queue.py
from app.worker import celery_app

@celery_app.task(name="transcribe_and_process")
def transcribe_and_process(job_id: str, media_id: str):
    # 1. Load media file
    # 2. Extract audio if video
    # 3. Transcribe with Whisper
    # 4. Feed to processor.process_with_quality_control()
    # 5. Update job status
    # 6. Return results
    pass
```

### 6. Integration with Existing Pipeline

```python
# Connect to existing processor
from app.services.processor import AIChiefOfStaffProcessor

# After transcription
transcript = transcribe_audio(file_path)

# Feed into existing pipeline
result = processor.process_with_quality_control(transcript)

# Store results linked to job_id
```

### 7. Error Handling

- File size validation (max 100MB)
- Format validation (supported formats only)
- Transcription failures (retry logic)
- Storage cleanup (delete temp files after 24h)

### 8. Performance Considerations

- Stream large file uploads (chunked transfer)
- Use FFmpeg for efficient audio extraction
- Cache transcriptions (avoid re-processing same file)
- Rate limiting for Whisper API calls

### 9. Testing

```bash
# Test audio upload
curl -X POST http://localhost:8000/api/v1/media/upload \
  -F "file=@test.mp3"

# Test video upload
curl -X POST http://localhost:8000/api/v1/media/upload \
  -F "file=@meeting.mp4"

# Test transcription
curl -X POST http://localhost:8000/api/v1/media/transcribe/{media_id}

# Check status
curl http://localhost:8000/api/v1/media/status/{job_id}
```

### 10. Docker Configuration

```dockerfile
# Update Dockerfile to include FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
```

## Timeline
- Day 1: Setup endpoints and database schema
- Day 2: Implement Whisper integration
- Day 3: Build Celery tasks and testing
- Day 4: Integration with existing pipeline
- Day 5: Bug fixes and optimization

## Success Criteria
- ✅ Upload video/audio files
- ✅ Transcribe with 95%+ accuracy
- ✅ Process transcriptions through AI pipeline
- ✅ Return tasks/decisions/risks
- ✅ Handle errors gracefully
