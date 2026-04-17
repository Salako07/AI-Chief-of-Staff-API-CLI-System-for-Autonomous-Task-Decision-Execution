# AI Chief of Staff - Development Guide

## 🎯 Quick Start for Teams

### Backend Team (Media Extraction)
**Your Mission:** Add video/audio transcription to the AI Chief of Staff pipeline.

**Start Here:**
1. Read `/docs/media-extraction-spec.md`
2. Review `/docs/COORDINATION.md`
3. Check existing code: `/app/services/processor.py` (this is what you'll integrate with)
4. Your workspace: `/app/media/` (already created)

**Key Files to Create:**
- `app/media/routes.py` - FastAPI endpoints
- `app/media/transcription.py` - Whisper API integration
- `app/media/processor.py` - FFmpeg audio extraction
- `app/services/media_queue.py` - Celery async tasks

**Quick Test:**
```bash
# Test existing API
curl http://localhost:8000/api/v1/health

# Your new endpoints will be:
# POST /api/v1/media/upload
# POST /api/v1/media/transcribe/:id
# GET /api/v1/media/status/:id
```

---

### Frontend Team (Web Application)
**Your Mission:** Build a Tesla-worthy web interface for the AI Chief of Staff.

**Start Here:**
1. Read `/docs/webapp-spec.md`
2. Review `/docs/COORDINATION.md`
3. Test the API: http://localhost:8000/docs
4. Your workspace: Create `webapp/` directory at project root

**Quick Setup:**
```bash
# Create Next.js app
cd webapp
npx create-next-app@latest . --typescript --tailwind --app
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install framer-motion lucide-react
npm install @tanstack/react-query
```

**API Endpoints You'll Use:**
```typescript
// Existing (working now)
POST http://localhost:8000/api/v1/process
GET  http://localhost:8000/api/v1/health

// New (backend team building)
POST http://localhost:8000/api/v1/media/upload
POST http://localhost:8000/api/v1/media/transcribe/:id
GET  http://localhost:8000/api/v1/media/status/:id
```

---

## 📋 Current System Overview

### What's Already Built

#### ✅ AI Processing Pipeline
- **Location:** `app/services/processor.py`
- **What it does:** Extracts tasks, decisions, risks from text
- **How to use:**
```python
from app.services.processor import AIChiefOfStaffProcessor

processor = AIChiefOfStaffProcessor(llm, tools, db)
result = processor.process_with_quality_control("Your text here")

# Returns:
{
  "run_id": "uuid",
  "tasks": [...],
  "decisions": [...],
  "risks": [...],
  "summary": "..."
}
```

#### ✅ API Endpoints
- **Location:** `app/api/routes.py`
- **Working endpoints:**
  - `POST /api/v1/process` - Process text
  - `GET /api/v1/health` - Health check

#### ✅ Async Processing
- **Location:** `app/services/queue.py`
- **What it does:** Celery tasks for background processing
- **Infrastructure:** Redis + PostgreSQL

#### ✅ Slack Integration
- **Location:** `app/tools/slack_tool.py`
- **What it does:** Sends formatted summaries to Slack

#### ✅ Docker Deployment
- **Location:** `docker-compose.yml`, `Dockerfile`
- **Services:** API, Worker, Redis, PostgreSQL, Flower

---

## 🏗️ Architecture Diagram

```
┌─────────────────┐
│   Web App       │ ← Frontend Team builds this
│  (Next.js 14)   │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────┐
│   FastAPI       │ ← Backend adds media endpoints here
│   (Python)      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────────────┐
│ Text   │ │ Media Upload   │ ← Backend Team
│ Input  │ │ + Transcription│    builds this
└───┬────┘ └────────┬───────┘
    │               │
    │               ▼
    │        ┌─────────────┐
    │        │   Whisper   │ ← OpenAI API
    │        │     API     │
    │        └──────┬──────┘
    │               │
    └───────┬───────┘
            │ Transcribed Text
            ▼
    ┌───────────────┐
    │  AI Pipeline  │ ← Already built
    │  (Processor)  │    (no changes needed)
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │   Results     │
    │ (Tasks/Risks) │
    └───────┬───────┘
            │
     ┌──────┴──────┐
     │             │
     ▼             ▼
┌─────────┐  ┌──────────┐
│  Slack  │  │  Web App │
└─────────┘  └──────────┘
```

---

## 🔧 Development Environment

### Prerequisites
- Python 3.11+
- Node.js 18+ (Frontend only)
- Docker & Docker Compose
- Redis (via Docker)
- PostgreSQL (via Docker)

### Backend Setup
```bash
# Already running! Just verify:
docker-compose ps

# Should see:
# - ai_chief_api (port 8000)
# - worker (Celery)
# - redis (port 6379)
# - postgres (port 5432)
# - flower (port 5555)

# Test API
curl http://localhost:8000/api/v1/health
```

### Frontend Setup (To Be Created)
```bash
# In project root
mkdir webapp
cd webapp

# Initialize Next.js
npx create-next-app@latest . --typescript --tailwind --app

# Install dependencies
npm install
npm run dev  # Starts on http://localhost:3000
```

---

## 📝 Coding Standards

### Backend (Python)
```python
# Use type hints
def process_media(file_path: str) -> dict:
    """Process media file and return results."""
    pass

# Follow existing patterns
from app.services.processor import AIChiefOfStaffProcessor

# Use Pydantic for validation
from pydantic import BaseModel

class MediaUpload(BaseModel):
    filename: str
    size_bytes: int

# Async for I/O operations
async def upload_file(file: UploadFile):
    pass

# Logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing file: {filename}")
```

### Frontend (TypeScript)
```typescript
// Use TypeScript strictly
interface Task {
  id: string;
  title: string;
  priority: "low" | "medium" | "high";
}

// React Server Components (Next.js 14)
export default async function Page() {
  const data = await fetchData();
  return <div>{data}</div>;
}

// Client components when needed
'use client';
import { useState } from 'react';

// Tailwind for styling
<div className="flex items-center justify-center bg-black text-white">

// Use shadcn/ui components
import { Button } from "@/components/ui/button";
```

---

## 🧪 Testing

### Backend Testing
```bash
# Run tests
pytest

# Specific module
pytest app/media/tests/

# With coverage
pytest --cov=app/media
```

### Frontend Testing
```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Type checking
npm run type-check
```

---

## 📊 Progress Tracking

### Backend Milestones
- [ ] Day 1: Media upload endpoint working
- [ ] Day 2: Whisper API integration complete
- [ ] Day 3: Celery async processing working
- [ ] Day 4: Integration with AI pipeline
- [ ] Day 5: Testing and bug fixes

### Frontend Milestones
- [ ] Day 1-2: Project setup + landing page
- [ ] Day 3-4: Dashboard layout
- [ ] Day 5-7: API integration
- [ ] Week 2: Media upload UI
- [ ] Week 3: Polish and launch

---

## 🚨 Common Issues & Solutions

### Backend Issues

**Issue:** "Module not found"
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
docker-compose restart api worker
```

**Issue:** "Whisper API authentication failed"
```bash
# Solution: Check .env file
cat .env | grep OPENAI_API_KEY
# Should not be "test-key..."
```

**Issue:** "FFmpeg not found"
```bash
# Solution: Rebuild Docker image
docker-compose build api
```

### Frontend Issues

**Issue:** "Cannot connect to API"
```typescript
// Solution: Check CORS and API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

**Issue:** "Tailwind classes not working"
```bash
# Solution: Restart dev server
npm run dev
```

---

## 📞 Getting Help

### Documentation
- **Backend:** See `/docs/media-extraction-spec.md`
- **Frontend:** See `/docs/webapp-spec.md`
- **API Docs:** http://localhost:8000/docs
- **Coordination:** See `/docs/COORDINATION.md`

### Code Examples
```bash
# Backend example: Test existing processor
python -c "
from app.services.processor import AIChiefOfStaffProcessor
from crewai import LLM

llm = LLM(model='gpt-4o-mini')
processor = AIChiefOfStaffProcessor(llm, [], None)
result = processor.process_with_quality_control('Meeting with John on Friday at 3pm')
print(result)
"

# Frontend example: Test API from browser console
fetch('http://localhost:8000/api/v1/health')
  .then(r => r.json())
  .then(console.log)
```

### Quick Reference

**Backend File Structure:**
```
app/
├── api/
│   └── routes.py         # FastAPI routes
├── services/
│   ├── processor.py      # AI pipeline (DON'T MODIFY)
│   └── queue.py          # Celery tasks
├── media/                # YOUR WORKSPACE
│   ├── routes.py         # Media endpoints
│   ├── transcription.py  # Whisper integration
│   └── processor.py      # FFmpeg handling
```

**Frontend File Structure:**
```
webapp/
├── src/
│   ├── app/              # Next.js pages
│   ├── components/       # React components
│   ├── lib/              # Utilities
│   └── types/            # TypeScript types
```

---

## 🎉 Ready to Start?

### Backend Team - Next Steps:
1. ✅ Read this file
2. ✅ Read `/docs/media-extraction-spec.md`
3. ▶️ Create `app/media/routes.py` with upload endpoint
4. ⏸️ Test upload with curl
5. ⏸️ Implement Whisper transcription

### Frontend Team - Next Steps:
1. ✅ Read this file
2. ✅ Read `/docs/webapp-spec.md`
3. ▶️ Create `webapp/` directory
4. ▶️ Initialize Next.js project
5. ⏸️ Build landing page

---

**Questions?** Check `/docs/COORDINATION.md` for communication channels!

**Let's build something amazing! 🚀**
