"""
services/stt.py — Speech-to-text services.

Records audio from the microphone until silence is detected (or the max
duration is reached), then transcribes the recording using either:
- OpenAI Whisper API, or
- Local faster-whisper inference.
"""

from __future__ import annotations

import io
import logging
import tempfile
from typing import Protocol

import numpy as np
import sounddevice as sd
import soundfile as sf
from openai import OpenAI

from config import AudioConfig, STTConfig

logger = logging.getLogger(__name__)

# RMS threshold below which audio is considered silence
_SILENCE_RMS_THRESHOLD = 300


class _AudioRecorder:
    """Shared microphone recording helper for STT backends."""

    def __init__(self, stt_cfg: STTConfig, audio_cfg: AudioConfig) -> None:
        self._stt_cfg = stt_cfg
        self._audio_cfg = audio_cfg

    def record(self) -> np.ndarray | None:
        """Record audio frames, stopping on silence or max duration."""
        sample_rate = self._audio_cfg.sample_rate
        silence_timeout = self._stt_cfg.silence_timeout
        max_seconds = self._stt_cfg.max_seconds
        chunk_size = int(sample_rate * 0.1)  # 100 ms chunks

        frames: list[np.ndarray] = []
        silent_duration = 0.0
        total_duration = 0.0
        recording_started = False

        logger.info("Recording… (speak now)")

        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            device=self._audio_cfg.input_device,
            blocksize=chunk_size,
        ) as stream:
            while total_duration < max_seconds:
                chunk, _ = stream.read(chunk_size)
                rms = _rms(chunk)
                frames.append(chunk.copy())
                total_duration += chunk_size / sample_rate

                if rms > _SILENCE_RMS_THRESHOLD:
                    recording_started = True
                    silent_duration = 0.0
                elif recording_started:
                    silent_duration += chunk_size / sample_rate
                    if silent_duration >= silence_timeout:
                        logger.debug("Silence detected — stopping recording.")
                        break

        if not recording_started:
            return None

        return np.concatenate(frames, axis=0)


class STTService(Protocol):
    """Protocol for speech-to-text services."""

    def record_and_transcribe(self) -> str:
        """Record a user utterance and return the transcript."""


class WhisperAPIService:
    """Speech-to-text using the OpenAI Whisper API."""

    def __init__(self, stt_cfg: STTConfig, audio_cfg: AudioConfig) -> None:
        self._cfg = stt_cfg
        self._audio_cfg = audio_cfg
        self._recorder = _AudioRecorder(stt_cfg, audio_cfg)
        self._client = OpenAI(api_key=stt_cfg.api_key)

    def record_and_transcribe(self) -> str:
        """Record until silence, then send to Whisper API."""
        audio_data = self._recorder.record()
        if audio_data is None or len(audio_data) == 0:
            logger.warning("No audio captured.")
            return ""
        return self._transcribe(audio_data)

    def _transcribe(self, audio: np.ndarray) -> str:
        """Send recorded audio to Whisper API and return transcript."""
        buf = io.BytesIO()
        sf.write(buf, audio, self._audio_cfg.sample_rate, format="WAV", subtype="PCM_16")
        buf.seek(0)
        buf.name = "recording.wav"

        logger.info("Sending audio to Whisper API…")
        response = self._client.audio.transcriptions.create(
            model=self._cfg.model,
            file=buf,
        )
        text = response.text.strip()
        logger.info("Transcript: %s", text)
        return text


class WhisperLocalService:
    """Speech-to-text using local faster-whisper inference."""

    def __init__(self, stt_cfg: STTConfig, audio_cfg: AudioConfig) -> None:
        from faster_whisper import WhisperModel

        self._cfg = stt_cfg
        self._audio_cfg = audio_cfg
        self._recorder = _AudioRecorder(stt_cfg, audio_cfg)
        logger.info(
            "Initializing local Whisper model '%s' on %s (%s)",
            stt_cfg.local_model,
            stt_cfg.local_device,
            stt_cfg.local_compute_type,
        )
        self._model = WhisperModel(
            stt_cfg.local_model,
            device=stt_cfg.local_device,
            compute_type=stt_cfg.local_compute_type,
        )

    def record_and_transcribe(self) -> str:
        """Record until silence, then transcribe with local model."""
        audio_data = self._recorder.record()
        if audio_data is None or len(audio_data) == 0:
            logger.warning("No audio captured.")
            return ""

        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            sf.write(tmp.name, audio_data, self._audio_cfg.sample_rate, format="WAV", subtype="PCM_16")
            logger.info("Transcribing with local Whisper model…")
            segments, _ = self._model.transcribe(tmp.name)
            text = "".join(segment.text for segment in segments).strip()

        logger.info("Transcript: %s", text)
        return text


def create_stt_service(cfg: STTConfig, audio_cfg: AudioConfig) -> STTService:
    """Factory that returns the configured STT backend service."""
    backend = cfg.backend.lower()

    if backend == "api":
        return WhisperAPIService(cfg, audio_cfg)
    if backend == "local":
        return WhisperLocalService(cfg, audio_cfg)

    raise ValueError("Invalid STT_BACKEND. Expected 'api' or 'local'.")


def _rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
