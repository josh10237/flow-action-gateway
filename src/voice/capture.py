"""
Audio capture from microphone using PyAudio
"""
import pyaudio
import numpy as np
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
        self.wav_buffer = None
        self.wav_file = None
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000

    def start_recording(self):
        if self.is_recording:
            return

        self.is_recording = True

        while not self.audio_queue.empty():
            self.audio_queue.get()

        self.wav_buffer = io.BytesIO()
        self.wav_file = wave.open(self.wav_buffer, 'wb')
        self.wav_file.setnchannels(self.CHANNELS)
        self.wav_file.setsampwidth(self.p.get_sample_size(self.FORMAT))
        self.wav_file.setframerate(self.RATE)

        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False

        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            finally:
                self.stream = None

        if self.wav_file:
            try:
                self.wav_file.close()
            except Exception:
                pass

    def get_volume_level(self):
        if self.stream and self.stream.is_active():
            try:
                in_data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(in_data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_data**2))

                if rms < 30:
                    self.volume_level = 0
                else:
                    self.volume_level = min(100, int((rms / 300) * 100))

                if self.is_recording:
                    self.audio_queue.put(in_data)
                    if self.wav_file:
                        self.wav_file.writeframes(in_data)
            except Exception:
                pass

        return self.volume_level

    def get_audio_data(self):
        if self.wav_buffer:
            return self.wav_buffer.getvalue()
        return b''

    def cleanup(self):
        self.stop_recording()
        try:
            self.p.terminate()
        except Exception:
            pass
