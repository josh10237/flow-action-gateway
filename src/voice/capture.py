"""
Audio capture from microphone using PyAudio
"""
import pyaudio
import numpy as np
import threading
import wave
import io
from queue import Queue


class AudioCapture:
    """Captures audio from microphone and provides volume levels."""

    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_queue = Queue()
        self.volume_level = 0

        # WAV encoding (created during recording)
        self.wav_buffer = None
        self.wav_file = None

        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000  # 16kHz for Whisper

    def start_recording(self):
        """Start capturing audio from microphone."""
        if self.is_recording:
            return

        self.is_recording = True

        # Clear any leftover audio from previous session
        while not self.audio_queue.empty():
            self.audio_queue.get()

        # Pre-create WAV buffer and start encoding during capture
        self.wav_buffer = io.BytesIO()
        self.wav_file = wave.open(self.wav_buffer, 'wb')
        self.wav_file.setnchannels(self.CHANNELS)
        self.wav_file.setsampwidth(self.p.get_sample_size(self.FORMAT))
        self.wav_file.setframerate(self.RATE)

        # Open audio stream in BLOCKING mode (no callback thread)
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

    def stop_recording(self):
        """Stop capturing audio."""
        if not self.is_recording:
            return

        self.is_recording = False

        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass  # Ignore errors during cleanup
            finally:
                self.stream = None

        # Close WAV file to finalize encoding
        if self.wav_file:
            try:
                self.wav_file.close()
            except Exception:
                pass  # Ignore errors during cleanup

    def get_volume_level(self):
        """Get current audio volume level (0-100)."""
        # Read audio and update volume in blocking mode
        if self.stream and self.stream.is_active():
            try:
                # Read one chunk from mic
                in_data = self.stream.read(self.CHUNK, exception_on_overflow=False)

                # Convert to numpy and calculate RMS
                audio_data = np.frombuffer(in_data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_data**2))

                # Update volume level with high sensitivity
                if rms < 30:
                    self.volume_level = 0
                else:
                    # Very sensitive: 300 RMS = 100%
                    self.volume_level = min(100, int((rms / 300) * 100))

                # Only store audio if we're actively recording
                if self.is_recording:
                    self.audio_queue.put(in_data)
                    # Write frame to WAV file as we capture (parallel encoding)
                    if self.wav_file:
                        self.wav_file.writeframes(in_data)
            except Exception:
                pass  # Ignore read errors

        return self.volume_level

    def get_audio_data(self):
        """Get all recorded audio data as pre-encoded WAV bytes."""
        # Return the already-encoded WAV file
        if self.wav_buffer:
            return self.wav_buffer.getvalue()
        return b''

    def cleanup(self):
        """Clean up PyAudio resources."""
        self.stop_recording()
        try:
            self.p.terminate()
        except Exception:
            pass  # Ignore errors during cleanup
