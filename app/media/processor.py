"""
FFmpeg-based media processing for audio extraction and metadata.
"""
import os
import subprocess
import logging
from typing import Dict, Optional
from app.media.schemas import MediaFileMetadata

logger = logging.getLogger(__name__)


class MediaProcessor:
    """
    FFmpeg wrapper for media processing.

    Handles audio extraction from video files,
    format conversion, and metadata extraction.
    """

    def __init__(self):
        """Initialize media processor and verify FFmpeg availability."""
        self._verify_ffmpeg()
        logger.info("Media processor initialized")

    def _verify_ffmpeg(self):
        """
        Verify FFmpeg is installed and accessible.

        Raises:
            RuntimeError: FFmpeg not found or not executable
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                raise RuntimeError("FFmpeg command failed")

            logger.info("FFmpeg verified successfully")

        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg not found. Please install: apt-get install ffmpeg (Linux) or brew install ffmpeg (macOS)"
            )
        except Exception as e:
            raise RuntimeError(f"FFmpeg verification failed: {str(e)}")

    def extract_audio(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        format: str = "mp3",
        bitrate: str = "192k"
    ) -> str:
        """
        Extract audio from video file or convert audio format.

        Args:
            input_path: Path to input video/audio file
            output_path: Path for output audio file (auto-generated if None)
            format: Output audio format (mp3, wav, m4a)
            bitrate: Audio bitrate (e.g., '192k', '320k')

        Returns:
            Path to extracted audio file

        Raises:
            FileNotFoundError: Input file not found
            Exception: FFmpeg processing errors
        """
        try:
            # Validate input file
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")

            # Generate output path if not provided
            if output_path is None:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}_audio.{format}"

            logger.info(f"Extracting audio: {input_path} -> {output_path}")

            # Build FFmpeg command
            # -i: input file
            # -vn: disable video
            # -acodec: audio codec (libmp3lame for mp3)
            # -ab: audio bitrate
            # -y: overwrite output file
            command = [
                "ffmpeg",
                "-i", input_path,
                "-vn",  # No video
                "-acodec", self._get_codec(format),
                "-ab", bitrate,
                "-y",  # Overwrite
                output_path
            ]

            # Execute FFmpeg
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
                raise Exception(f"FFmpeg failed: {error_msg}")

            # Verify output file exists
            if not os.path.exists(output_path):
                raise Exception("Output file not created")

            output_size = os.path.getsize(output_path)
            logger.info(f"Audio extraction successful: {output_path} ({output_size} bytes)")

            return output_path

        except FileNotFoundError:
            logger.error(f"Input file not found: {input_path}")
            raise

        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg timeout (5 min) for: {input_path}")
            raise Exception("Audio extraction timeout (file too large or corrupted)")

        except Exception as e:
            logger.error(f"Audio extraction failed: {str(e)}", exc_info=True)
            raise

    def get_metadata(self, file_path: str) -> MediaFileMetadata:
        """
        Extract metadata from media file using ffprobe.

        Args:
            file_path: Path to media file

        Returns:
            MediaFileMetadata with duration, format, codec, bitrate, etc.

        Raises:
            FileNotFoundError: File not found
            Exception: ffprobe errors
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            logger.info(f"Extracting metadata: {file_path}")

            # Build ffprobe command
            command = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path
            ]

            # Execute ffprobe
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise Exception(f"ffprobe failed: {result.stderr}")

            # Parse JSON output
            import json
            data = json.loads(result.stdout)

            # Extract metadata
            format_info = data.get("format", {})
            audio_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "audio"),
                {}
            )

            metadata = MediaFileMetadata(
                duration_seconds=int(float(format_info.get("duration", 0))),
                format=format_info.get("format_name"),
                codec=audio_stream.get("codec_name"),
                bitrate=int(format_info.get("bit_rate", 0)),
                sample_rate=int(audio_stream.get("sample_rate", 0)) if audio_stream.get("sample_rate") else None,
                channels=audio_stream.get("channels")
            )

            logger.info(f"Metadata extracted: duration={metadata.duration_seconds}s, format={metadata.format}")

            return metadata

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise

        except subprocess.TimeoutExpired:
            logger.error(f"ffprobe timeout for: {file_path}")
            raise Exception("Metadata extraction timeout")

        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}", exc_info=True)
            raise

    def _get_codec(self, format: str) -> str:
        """
        Get FFmpeg audio codec for output format.

        Args:
            format: Output format (mp3, wav, m4a, ogg)

        Returns:
            FFmpeg codec name
        """
        codec_map = {
            "mp3": "libmp3lame",
            "wav": "pcm_s16le",
            "m4a": "aac",
            "ogg": "libvorbis"
        }

        return codec_map.get(format.lower(), "libmp3lame")


def test_media_processor():
    """
    Test function to validate FFmpeg integration.

    Usage:
        python -c "from app.media.processor import test_media_processor; test_media_processor()"
    """
    try:
        processor = MediaProcessor()
        print("✅ Media processor initialized successfully")
        print("✅ FFmpeg is available")

        # Note: Requires an actual media file to test processing
        print("⚠️ To test processing, call processor.extract_audio('path/to/video.mp4')")

        return processor

    except Exception as e:
        print(f"❌ Media processor initialization failed: {e}")
        raise


if __name__ == "__main__":
    test_media_processor()
