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
        if not audio_data:
            return ""

        wav_buffer = io.BytesIO(audio_data)
        wav_buffer.seek(0)
        wav_buffer.name = "audio.wav"

        transcript = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_buffer,
            language="en"
        )

        text = transcript.text.strip()

        if len(text) < 3:
            return ""

        return text
