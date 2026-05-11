"""
OpenAI Whisper API integration for audio transcription.
"""
import os
import logging
from typing import Dict, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """
    Wrapper for OpenAI Whisper API transcription.

    Handles audio file transcription with language detection,
    timestamps, and error handling.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Whisper transcriber.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY not set")

        self.client = OpenAI(api_key=self.api_key)
        logger.info("Whisper transcriber initialized")

    def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0
    ) -> Dict[str, str]:
        """
        Transcribe audio file using OpenAI Whisper API.

        Args:
            audio_file_path: Path to audio file (mp3, wav, m4a, etc.)
            language: Language code (e.g., 'en', 'es'). Auto-detected if None.
            prompt: Optional text to guide transcription style/context
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)

        Returns:
            Dictionary with transcription text and metadata:
            {
                "text": "Transcribed text here...",
                "language": "en",
                "duration": 120.5
            }

        Raises:
            FileNotFoundError: Audio file not found
            ValueError: Invalid audio file format
            Exception: API errors or transcription failures
        """
        try:
            # Validate file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

            # Get file size for logging
            file_size = os.path.getsize(audio_file_path)
            logger.info(f"Transcribing audio file: {audio_file_path} ({file_size} bytes)")

            # Open audio file and call Whisper API
            with open(audio_file_path, "rb") as audio_file:
                # Build request parameters with quality enhancements
                # Force English to prevent Welsh/foreign language hallucinations
                # Use temperature=0.0 for deterministic, non-random output
                # Add context prompt to guide transcription
                params = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "language": language or "en",  # FORCE ENGLISH - prevents hallucinations
                    "temperature": 0.0,  # Override parameter - deterministic output
                    "prompt": prompt or "This is a business meeting or conversation in English discussing tasks, decisions, projects, and planning."  # Context hint
                }

                # Call Whisper API
                response = self.client.audio.transcriptions.create(**params)

            # Extract transcription text
            transcription_text = response.text

            # Validate transcription quality (detect hallucinations)
            if not self._validate_transcription_quality(transcription_text):
                logger.warning("Low quality transcription detected, may contain hallucinations")
                raise Exception(
                    "Transcription quality too low - possible hallucination detected. "
                    "This often happens with poor audio quality, background noise, or very quiet recordings. "
                    "Please ensure: 1) Clear audio with minimal background noise, "
                    "2) Speaker is audible, 3) Recording is not silent/empty."
                )

            logger.info(f"Transcription successful: {len(transcription_text)} characters")

            return {
                "text": transcription_text,
                "language": language or "auto",
                "duration": None  # Whisper API doesn't return duration
            }

        except FileNotFoundError:
            logger.error(f"Audio file not found: {audio_file_path}")
            raise

        except Exception as e:
            logger.error(f"Transcription failed for {audio_file_path}: {str(e)}", exc_info=True)
            raise Exception(f"Transcription failed: {str(e)}")

    def _validate_transcription_quality(self, text: str) -> bool:
        """
        Check if transcription is valid or likely hallucinated.

        Red flags for hallucinations:
        - Too short (< 10 chars)
        - Welsh repetition ("Iawn", "Helo", "Rwy'n")
        - Too few unique words (repetitive)
        - Excessive same word repetition

        Returns:
            bool: True if quality is acceptable, False if likely hallucination
        """
        if not text or len(text) < 10:
            return False

        # Check for Welsh hallucination keywords
        welsh_keywords = ["Iawn", "Helo", "Rwy'n", "gobeithio", "bawb", "byddwn"]
        welsh_count = sum(text.count(keyword) for keyword in welsh_keywords)
        if welsh_count > 5:
            logger.warning(f"Welsh hallucination detected (count: {welsh_count})")
            return False

        # Check for excessive repetition
        words = text.split()
        if len(words) > 20:
            unique_words = len(set(words))
            repetition_ratio = unique_words / len(words)
            if repetition_ratio < 0.3:  # Less than 30% unique words
                logger.warning(f"Excessive repetition detected (ratio: {repetition_ratio:.2f})")
                return False

        # Check for single word spam (e.g., "Iawn. Iawn. Iawn. Iawn...")
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        for word, count in word_counts.items():
            if count > len(words) * 0.5:  # Single word is >50% of transcript
                logger.warning(f"Single word spam detected: '{word}' repeated {count} times")
                return False

        return True

    def transcribe_with_timestamps(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Transcribe with word-level timestamps (verbose mode).

        Note: OpenAI Whisper API currently doesn't support verbose_json
        via the Python SDK. This method is a placeholder for future support.

        Args:
            audio_file_path: Path to audio file
            language: Language code (optional)

        Returns:
            Dictionary with transcription and timestamps
        """
        # Currently, OpenAI Whisper API doesn't expose timestamps via SDK
        # Fallback to regular transcription
        logger.warning("Timestamp support not available via OpenAI API. Using standard transcription.")

        result = self.transcribe(audio_file_path, language=language)
        result["timestamps"] = None

        return result


def test_whisper_transcription():
    """
    Test function to validate Whisper API integration.

    Usage:
        python -c "from app.media.transcription import test_whisper_transcription; test_whisper_transcription()"
    """
    try:
        transcriber = WhisperTranscriber()
        print("✅ Whisper transcriber initialized successfully")
        print(f"✅ Using API key: {transcriber.api_key[:10]}...")

        # Note: Requires an actual audio file to test transcription
        print("⚠️ To test transcription, call transcriber.transcribe('path/to/audio.mp3')")

        return transcriber

    except Exception as e:
        print(f"❌ Whisper transcriber initialization failed: {e}")
        raise


if __name__ == "__main__":
    test_whisper_transcription()
