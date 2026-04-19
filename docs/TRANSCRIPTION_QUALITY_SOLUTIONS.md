# Transcription Quality Issues & Solutions

## 🔴 Problem Analysis

**Current Issue:**
The Whisper API transcriptions are producing poor quality output with:
- Welsh language hallucinations ("Rwy'n gobeithio...")
- Repetitive nonsensical text ("Iawn. Iawn. Iawn...")
- Not transcribing actual English audio content correctly

**Example of Bad Output:**
```
Rwy'n gobeithio y byddwn yn gweithio'n fawr iawn, ond rwy'n gobeithio...
Helo. Helo bawb. Helo bawb. Helo. Helo bawb...
Iawn. Iawn. Iawn. Iawn. Iawn. Iawn. Iawn...
```

**Root Causes:**
1. **No Language Specification** - Whisper is auto-detecting language incorrectly
2. **Poor Audio Quality** - Background noise, low volume, or encoding issues
3. **No Audio Preprocessing** - Raw audio fed directly to Whisper without optimization
4. **Missing Whisper Parameters** - Not using prompt hints or temperature controls
5. **Suboptimal Model** - Using default Whisper without considering alternatives

---

## ✅ Solution 1: Enhanced Whisper API Configuration (Quick Fix)

### **Implementation Time:** 30 minutes
### **Effectiveness:** 60-80% improvement
### **Cost:** No additional cost

### **Changes Needed:**

#### 1. Force English Language Detection
```python
# app/media/transcription.py - Line 45

response = self.client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
    language="en",  # ✅ FORCE ENGLISH - prevents Welsh hallucinations
    temperature=0.0,  # ✅ Deterministic output - reduces randomness
    prompt="This is a business meeting recording in English discussing tasks, decisions, and project planning."  # ✅ Context hint
)
```

#### 2. Add Audio Preprocessing with FFmpeg
```python
# app/media/processor.py - New method

def preprocess_audio_for_whisper(self, input_path: str) -> str:
    """
    Optimize audio for Whisper transcription.

    Improvements:
    - Convert to 16kHz mono (Whisper's preferred format)
    - Apply noise reduction
    - Normalize audio levels
    - Remove silence
    """
    output_path = f"{input_path}_preprocessed.wav"

    command = [
        "ffmpeg", "-i", input_path,
        "-ar", "16000",  # 16kHz sample rate
        "-ac", "1",  # Mono channel
        "-af", "highpass=f=200,lowpass=f=3000,volume=2.0",  # Audio filters
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-y", output_path
    ]

    subprocess.run(command, capture_output=True, timeout=60)
    return output_path
```

#### 3. Implement Quality Validation
```python
# app/services/media_queue.py - After transcription

def validate_transcription(transcription: str) -> bool:
    """Check if transcription is valid or hallucinated."""

    # Red flags for bad transcription
    red_flags = [
        len(transcription) < 10,  # Too short
        transcription.count("Iawn") > 5,  # Welsh repetition
        transcription.count("Helo") > 5,  # Welsh greetings
        len(set(transcription.split())) < 10,  # Too few unique words
    ]

    if any(red_flags):
        raise Exception("Transcription quality too low - possible hallucination detected")

    return True
```

### **Pros:**
- ✅ Quick to implement
- ✅ No additional API costs
- ✅ Solves most common Whisper issues
- ✅ Works with existing infrastructure

### **Cons:**
- ⚠️ Still dependent on Whisper's quality
- ⚠️ May not fix very poor audio quality
- ⚠️ Requires FFmpeg audio filters knowledge

---

## ✅ Solution 2: Hybrid Approach - AssemblyAI + Whisper (Recommended)

### **Implementation Time:** 2-3 hours
### **Effectiveness:** 85-95% improvement
### **Cost:** $0.00025/second (~$1.50 per hour of audio)

### **Why AssemblyAI?**
- **Better accuracy** for English business conversations
- **Built-in speaker diarization** (identifies who's speaking)
- **Automatic punctuation** and proper formatting
- **No hallucinations** - more reliable than Whisper
- **Custom vocabulary** support for technical terms

### **Architecture:**

```
Audio Upload
    ↓
FFmpeg Preprocessing
    ↓
Primary: AssemblyAI API
    ↓ (if fails or low confidence)
Fallback: Whisper API with enhanced config
    ↓
Quality Validation
    ↓
AI Processing Pipeline
```

### **Implementation:**

#### 1. Add AssemblyAI SDK
```bash
# requirements.txt
assemblyai==0.17.0
```

#### 2. Create AssemblyAI Transcriber
```python
# app/media/assemblyai_transcription.py (NEW FILE)

import assemblyai as aai
import os

class AssemblyAITranscriber:
    def __init__(self):
        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

    def transcribe(self, audio_file_path: str) -> dict:
        """
        Transcribe using AssemblyAI with speaker diarization.
        """
        config = aai.TranscriptionConfig(
            speaker_labels=True,  # Identify speakers
            auto_chapters=True,  # Auto-segment by topic
            entity_detection=True,  # Detect names, dates, etc.
            sentiment_analysis=False,  # Optional
            language_code="en_us"
        )

        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(audio_file_path)

        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"AssemblyAI failed: {transcript.error}")

        # Format with speaker labels
        formatted_text = ""
        for utterance in transcript.utterances:
            formatted_text += f"Speaker {utterance.speaker}: {utterance.text}\n"

        return {
            "text": transcript.text,
            "formatted_text": formatted_text,
            "confidence": transcript.confidence,
            "words": len(transcript.words)
        }
```

#### 3. Update Media Queue with Hybrid Logic
```python
# app/services/media_queue.py - Enhanced transcription

try:
    # Try AssemblyAI first (more accurate)
    assemblyai_transcriber = AssemblyAITranscriber()
    result = assemblyai_transcriber.transcribe(audio_file_path)

    if result["confidence"] > 0.8:  # High confidence
        transcription_text = result["formatted_text"]
        logger.info(f"Used AssemblyAI (confidence: {result['confidence']})")
    else:
        raise Exception("Low confidence, fallback to Whisper")

except Exception as e:
    # Fallback to enhanced Whisper
    logger.warning(f"AssemblyAI failed, using Whisper: {e}")
    whisper_transcriber = WhisperTranscriber()
    result = whisper_transcriber.transcribe(
        audio_file_path,
        language="en",
        temperature=0.0,
        prompt="English business meeting"
    )
    transcription_text = result["text"]
```

### **Pros:**
- ✅ **Best accuracy** for English business audio
- ✅ **Speaker identification** (who said what)
- ✅ **No hallucinations** - much more reliable
- ✅ **Automatic fallback** to Whisper if needed
- ✅ Professional-grade quality

### **Cons:**
- ⚠️ Additional API cost (~$1.50/hour of audio)
- ⚠️ Requires AssemblyAI API key
- ⚠️ Slightly slower (2-3 minutes for 1 hour audio)

### **Cost Analysis:**
- 10 hours of meetings/month = $15/month
- 100 hours = $150/month
- Still cheaper than hiring a transcriptionist ($1-2/minute = $60-120/hour)

---

## ✅ Solution 3: Self-Hosted Faster-Whisper (Advanced)

### **Implementation Time:** 4-6 hours
### **Effectiveness:** 70-90% improvement
### **Cost:** GPU server costs (~$50-100/month)

### **Why Faster-Whisper?**
- **5x faster** than OpenAI's Whisper API
- **Full control** over model parameters
- **No API rate limits**
- **Works offline** - no internet dependency
- **Better for high-volume** processing

### **Technology Stack:**
- **faster-whisper** (CTranslate2 optimized)
- **whisper-large-v3** model
- **GPU acceleration** (CUDA/TensorRT)
- **Docker container** for isolation

### **Architecture:**

```
Docker Container: Faster-Whisper Service
    ↓
GPU-accelerated transcription (NVIDIA CUDA)
    ↓
Internal API endpoint
    ↓
Celery worker calls internal API
    ↓
AI processing pipeline
```

### **Implementation:**

#### 1. Create Faster-Whisper Service
```python
# app/media/faster_whisper_service.py (NEW FILE)

from faster_whisper import WhisperModel
import torch

class FasterWhisperService:
    def __init__(self):
        # Load model on GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        # Use large-v3 model for best accuracy
        self.model = WhisperModel(
            "large-v3",
            device=device,
            compute_type=compute_type,
            cpu_threads=4,
            num_workers=4
        )

    def transcribe(self, audio_path: str) -> dict:
        """
        Transcribe with advanced VAD and hallucination suppression.
        """
        segments, info = self.model.transcribe(
            audio_path,
            language="en",
            beam_size=5,  # Balance speed/accuracy
            vad_filter=True,  # Voice Activity Detection
            vad_parameters=dict(
                threshold=0.5,
                min_speech_duration_ms=250
            ),
            condition_on_previous_text=False,  # Reduce hallucinations
            temperature=0.0,
            compression_ratio_threshold=2.4,  # Detect repetition
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6
        )

        # Combine segments
        full_text = " ".join([segment.text for segment in segments])

        return {
            "text": full_text,
            "language": info.language,
            "duration": info.duration,
            "segments": len(list(segments))
        }
```

#### 2. Create Docker Service
```dockerfile
# Dockerfile.whisper (NEW FILE)

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.11 python3-pip ffmpeg

RUN pip install faster-whisper torch torchaudio

COPY app/media/faster_whisper_service.py /app/

CMD ["python3", "/app/faster_whisper_service.py"]
```

#### 3. Update docker-compose.yml
```yaml
# docker-compose.yml - Add whisper service

whisper:
  build:
    context: .
    dockerfile: Dockerfile.whisper
  container_name: ai_chief_whisper
  runtime: nvidia  # GPU support
  environment:
    - CUDA_VISIBLE_DEVICES=0
  volumes:
    - ./media_uploads:/media_uploads
  ports:
    - "8001:8001"
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### **Pros:**
- ✅ **5x faster** than OpenAI Whisper
- ✅ **No API costs** after initial setup
- ✅ **Full control** over parameters
- ✅ **Better for high volume** (unlimited usage)
- ✅ **Works offline**

### **Cons:**
- ⚠️ **Requires GPU** server ($50-100/month or one-time hardware cost)
- ⚠️ **Complex setup** - Docker, CUDA, GPU drivers
- ⚠️ **Maintenance overhead** - model updates, server management
- ⚠️ **Initial investment** in infrastructure

### **Cost Analysis:**
- **Cloud GPU:** AWS g4dn.xlarge = ~$0.50/hour = $360/month (24/7)
- **Spot instances:** ~$0.15/hour = $108/month
- **Own GPU:** RTX 3060 = $300 one-time + electricity
- **Break-even:** ~2000 hours of transcription vs AssemblyAI

---

## 📊 Solution Comparison

| Feature | Solution 1: Enhanced Whisper | Solution 2: AssemblyAI Hybrid ⭐ | Solution 3: Self-Hosted |
|---------|------------------------------|----------------------------------|-------------------------|
| **Implementation Time** | 30 mins | 2-3 hours | 4-6 hours |
| **Accuracy Improvement** | 60-80% | 85-95% | 70-90% |
| **Monthly Cost (100hrs)** | $0 | $150 | $100-360 |
| **Maintenance** | Low | Low | High |
| **Scalability** | Limited | High | Very High |
| **Speaker ID** | ❌ No | ✅ Yes | ⚠️ Possible |
| **Complexity** | ⭐ Easy | ⭐⭐ Medium | ⭐⭐⭐ Hard |
| **Best For** | Budget, low volume | Most users ⭐ | High volume, offline |

---

## 🎯 Recommended Action Plan

### **Immediate (Today):**
**Implement Solution 1 - Enhanced Whisper Config**
- Add `language="en"` parameter
- Add context prompt
- Implement quality validation
- **Expected improvement:** 60-80%
- **Time:** 30 minutes

### **Short-term (This Week):**
**Implement Solution 2 - AssemblyAI Hybrid**
- Sign up for AssemblyAI (free tier: 5 hours/month)
- Integrate as primary transcription service
- Keep Whisper as fallback
- **Expected improvement:** 85-95%
- **Time:** 2-3 hours

### **Long-term (Optional):**
**Evaluate Solution 3 - Self-Hosted**
- Only if processing >500 hours/month
- Requires dedicated GPU infrastructure
- Best for enterprise scale

---

## 🛠️ Implementation Steps (Solution 2 - Recommended)

### Step 1: Get AssemblyAI API Key
```bash
# Sign up at https://www.assemblyai.com/
# Free tier: 5 hours/month
# Paid: $0.00025/second (~$0.90/hour)
```

### Step 2: Install Dependencies
```bash
pip install assemblyai==0.17.0
```

### Step 3: Add to .env
```bash
ASSEMBLYAI_API_KEY=your_api_key_here
```

### Step 4: Create AssemblyAI Transcriber
```bash
# Create: app/media/assemblyai_transcription.py
# (Code provided above)
```

### Step 5: Update Media Queue
```bash
# Modify: app/services/media_queue.py
# Add hybrid logic (AssemblyAI primary, Whisper fallback)
```

### Step 6: Test
```bash
# Upload test audio via webapp
# Check transcription quality
# Monitor confidence scores
```

---

## 📈 Expected Results

### Before (Current):
```
❌ "Rwy'n gobeithio y byddwn yn gweithio..."
❌ "Iawn. Iawn. Iawn. Iawn. Iawn. Iawn..."
❌ "Helo bawb. Helo. Helo bawb. Helo..."
Quality: 0/10
```

### After Solution 1 (Enhanced Whisper):
```
✅ "Hello everyone. Okay, I think you can start now..."
⚠️ Some errors, but mostly correct English
Quality: 6/10
```

### After Solution 2 (AssemblyAI):
```
✅ "Speaker A: Hello everyone. Okay, I think we can start the meeting now.
     Speaker B: Great, let me share my screen..."
✅ Perfect punctuation, speaker labels, high accuracy
Quality: 9/10
```

---

## 💡 Quick Win Recommendations

1. **Immediate:** Implement Solution 1 (30 mins, free)
2. **This week:** Implement Solution 2 (2 hours, $15/month for 10hrs)
3. **Audio quality tips:**
   - Ask users to use external microphones
   - Recommend quiet recording environments
   - Provide audio quality guidelines on upload page

---

**Last Updated:** April 17, 2026
**Recommended Solution:** Solution 2 (AssemblyAI Hybrid) ⭐
**Implementation Priority:** High (poor transcription blocks core feature)
