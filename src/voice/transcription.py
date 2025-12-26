"""
Voice transcription using OpenAI Whisper API
"""
import io
from openai import OpenAI


class Transcriber:
    """Transcribes audio to text using Whisper."""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe audio bytes to text.

        Args:
            audio_data: Pre-encoded WAV audio bytes (from AudioCapture)
            sample_rate: Audio sample rate (ignored, WAV is already encoded)

        Returns:
            Transcribed text
        """
        if not audio_data:
            return ""

        # Audio is already WAV-encoded from AudioCapture
        wav_buffer = io.BytesIO(audio_data)
        wav_buffer.seek(0)
        wav_buffer.name = "audio.wav"  # Whisper API needs a filename

        # Call Whisper API
        transcript = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_buffer,
            language="en",  # Optional: specify language for faster processing
            prompt="File system commands, write file, read file, create directory"  # Hint for better accuracy
        )

        # Clean up common Whisper hallucinations
        text = transcript.text.strip()

        # Remove common single-word hallucinations that appear with silence
        hallucinations = ["you", "thank you", "thanks", "bye", "you.", "thank you.", "thanks."]
        if text.lower() in hallucinations:
            return ""

        # Filter out very short transcriptions (likely noise)
        if len(text) < 3:
            return ""

        return text
