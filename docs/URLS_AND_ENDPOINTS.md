# URLs and API Endpoints Reference

## 🌐 Application URLs

### Frontend (Next.js)
- **Landing Page:** http://localhost:3001
- **Media Upload:** http://localhost:3001/upload

### Backend (FastAPI)
- **API Base:** http://localhost:8000
- **API Documentation (Swagger):** http://localhost:8000/docs
- **API Documentation (ReDoc):** http://localhost:8000/redoc

### Monitoring
- **Celery Flower (Task Monitor):** http://localhost:5555

---

## 📡 API Endpoints

### Text Processing Endpoints

#### Process Text
```
POST http://localhost:8000/api/v1/process
Content-Type: application/json

{
  "text": "Your meeting notes or text here...",
  "source": "webapp_demo"
}

Response:
{
  "run_id": "uuid",
  "tasks": [...],
  "decisions": [...],
  "risks": [...],
  "summary": "..."
}
```

#### Check Task Status
```
GET http://localhost:8000/api/v1/task-status/{task_id}

Response:
{
  "state": "SUCCESS" | "PENDING" | "STARTED" | "FAILURE",
  "result": {...}
}
```

#### Health Check
```
GET http://localhost:8000/api/v1/health

Response:
{
  "status": "healthy",
  "service": "ai-chief-of-staff"
}
```

---

### Media Processing Endpoints

#### Upload Media File
```
POST http://localhost:8000/api/v1/media/upload
Content-Type: multipart/form-data

FormData:
  file: <audio/video file>

Response:
{
  "media_id": "uuid",
  "filename": "audio.mp3",
  "size_bytes": 1024000,
  "mime_type": "audio/mpeg",
  "status": "uploaded",
  "created_at": "2026-04-17T..."
}
```

#### Start Transcription
```
POST http://localhost:8000/api/v1/media/transcribe/{media_id}

Response:
{
  "job_id": "uuid",
  "media_id": "uuid",
  "status": "queued"
}
```

#### Check Transcription Status
```
GET http://localhost:8000/api/v1/media/status/{job_id}

Response:
{
  "job_id": "uuid",
  "media_id": "uuid",
  "status": "queued" | "processing" | "completed" | "failed",
  "progress": 75,
  "transcription_length": 1500,
  "processing_time_ms": 5000,
  "error_message": null
}
```

#### Get Transcription Results
```
GET http://localhost:8000/api/v1/media/result/{job_id}

Response:
{
  "job_id": "uuid",
  "run_id": "uuid",
  "media_id": "uuid",
  "transcription": "Full transcription text...",
  "tasks": [...],
  "decisions": [...],
  "risks": [...],
  "summary": "AI-generated summary...",
  "processing_time_ms": 5000
}
```

#### Media Service Health
```
GET http://localhost:8000/api/v1/media/health

Response:
{
  "status": "healthy",
  "service": "media-processing",
  "upload_dir": "/tmp/media_uploads",
  "max_file_size_mb": 100.0,
  "active_jobs": 0
}
```

---

## 🔧 Testing Commands

### Test Text Processing
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "We need to launch product Q2. John handles marketing. Budget: $50k. Risk: tight timeline.",
    "source": "cli_test"
  }'
```

### Test Media Upload
```bash
# Upload file
curl -X POST http://localhost:8000/api/v1/media/upload \
  -F "file=@path/to/audio.mp3"

# Start transcription (replace MEDIA_ID)
curl -X POST http://localhost:8000/api/v1/media/transcribe/MEDIA_ID

# Check status (replace JOB_ID)
curl http://localhost:8000/api/v1/media/status/JOB_ID

# Get results (replace JOB_ID)
curl http://localhost:8000/api/v1/media/result/JOB_ID
```

### Test Health Endpoints
```bash
# Main API health
curl http://localhost:8000/api/v1/health

# Media service health
curl http://localhost:8000/api/v1/media/health
```

---

## 🗄️ Database & Services

### PostgreSQL
- **Host:** localhost
- **Port:** 5432
- **Database:** ai_chief_of_staff
- **Connection String:** `postgresql://postgres:postgres@localhost:5432/ai_chief_of_staff`

### Redis
- **Host:** localhost
- **Port:** 6379
- **Connection String:** `redis://localhost:6379/0`

### Celery Worker
- **Broker:** Redis (redis://localhost:6379/0)
- **Backend:** Redis (redis://localhost:6379/0)
- **Tasks:**
  - `execute_actions` (existing workflow)
  - `app.services.media_queue.transcribe_media_task` (media transcription)
  - `app.services.media_queue.cleanup_old_media_files` (scheduled cleanup)

---

## 🎨 Frontend API Integration

### Text Demo (Landing Page)
```typescript
// src/app/page.tsx
const response = await fetch('http://localhost:8000/api/v1/process', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: inputText, source: 'webapp_demo' })
});
```

### Media Upload (Upload Page)
```typescript
// src/app/upload/page.tsx

// 1. Upload file
const formData = new FormData();
formData.append('file', selectedFile);
const uploadResponse = await fetch('http://localhost:8000/api/v1/media/upload', {
  method: 'POST',
  body: formData
});

// 2. Start transcription
const transcribeResponse = await fetch(
  `http://localhost:8000/api/v1/media/transcribe/${media_id}`,
  { method: 'POST' }
);

// 3. Poll status every 2 seconds
const statusResponse = await fetch(
  `http://localhost:8000/api/v1/media/status/${job_id}`
);

// 4. Get results when completed
const resultResponse = await fetch(
  `http://localhost:8000/api/v1/media/result/${job_id}`
);
```

---

## 🚀 Quick Start

1. **Start Backend:**
   ```bash
   docker-compose up -d
   ```

2. **Start Frontend:**
   ```bash
   cd webapp
   npm run dev
   ```

3. **Access Applications:**
   - Frontend: http://localhost:3001
   - API Docs: http://localhost:8000/docs
   - Flower Monitor: http://localhost:5555

---

## ✅ Verification Checklist

- [ ] Backend API running on port 8000
- [ ] Frontend running on port 3001
- [ ] API health check returns `{"status":"healthy"}`
- [ ] Media health check returns `{"status":"healthy"}`
- [ ] Text demo works on landing page
- [ ] Media upload page accessible at /upload
- [ ] CORS allows requests from http://localhost:3001
- [ ] Celery workers active and processing tasks

---

**Last Updated:** April 17, 2026
**Status:** All services operational ✅
