"""
services/audio.py — Audio playback service.

Plays MP3 audio bytes through the system speaker using sounddevice + soundfile.
"""

from __future__ import annotations

import io
import logging

import numpy as np
import sounddevice as sd
import soundfile as sf

from config import AudioConfig

logger = logging.getLogger(__name__)


class AudioService:
    """
    Plays raw audio bytes (MP3 or WAV) through the configured output device.

    Usage:
        svc = AudioService(audio_cfg)
        svc.play(audio_bytes)
    """

    def __init__(self, cfg: AudioConfig) -> None:
        self._cfg = cfg

    def play(self, audio_bytes: bytes) -> None:
        """
        Play audio bytes synchronously (blocks until playback finishes).

        Args:
            audio_bytes: Raw MP3 or WAV audio data.
        """
        buf = io.BytesIO(audio_bytes)
        data, sample_rate = sf.read(buf, dtype="float32")

        logger.info("Playing audio (%d frames @ %d Hz)…", len(data), sample_rate)

        sd.play(data, samplerate=sample_rate, device=self._cfg.output_device)
        sd.wait()
        logger.debug("Playback finished.")

    @staticmethod
    def list_devices() -> None:
        """Print all available audio devices to stdout. Useful for config."""
        print(sd.query_devices())
