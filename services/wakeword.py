"""
services/wakeword.py — Porcupine wake word detection service.

Listens continuously on the microphone and fires a callback when the
configured wake word is detected.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import pvporcupine
import sounddevice as sd
import numpy as np

from config import PorcupineConfig, AudioConfig

logger = logging.getLogger(__name__)


class WakeWordService:
    """
    Wraps Porcupine to provide continuous wake word listening.

    Usage:
        service = WakeWordService(porcupine_cfg, audio_cfg)
        service.listen(on_detected=my_callback)
    """

    def __init__(self, porcupine_cfg: PorcupineConfig, audio_cfg: AudioConfig) -> None:
        self._porcupine_cfg = porcupine_cfg
        self._audio_cfg = audio_cfg
        self._handle: pvporcupine.Porcupine | None = None

    def _build_handle(self) -> pvporcupine.Porcupine:
        if self._porcupine_cfg.keyword_path:
            logger.info("Using custom keyword model: %s", self._porcupine_cfg.keyword_path)
            return pvporcupine.create(
                access_key=self._porcupine_cfg.access_key,
                keyword_paths=[self._porcupine_cfg.keyword_path],
            )
        logger.info("Using built-in keyword: %s", self._porcupine_cfg.keyword)
        return pvporcupine.create(
            access_key=self._porcupine_cfg.access_key,
            keywords=[self._porcupine_cfg.keyword],
        )

    def listen(self, on_detected: Callable[[], None], stop_event=None) -> None:
        """
        Block and listen for the wake word.

        Args:
            on_detected: Called (no args) each time the wake word fires.
            stop_event:  Optional threading.Event; set it to stop gracefully.
        """
        self._handle = self._build_handle()
        frame_length = self._handle.frame_length
        sample_rate = self._handle.sample_rate

        logger.info("Wake word service ready — listening for '%s'", self._porcupine_cfg.keyword)

        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            device=self._audio_cfg.input_device,
            blocksize=frame_length,
        ) as stream:
            while True:
                if stop_event and stop_event.is_set():
                    logger.info("Wake word service stopped via stop_event.")
                    break

                pcm, _ = stream.read(frame_length)
                pcm_flat = pcm.flatten().tolist()
                result = self._handle.process(pcm_flat)

                if result >= 0:
                    logger.info("Wake word detected!")
                    on_detected()

    def cleanup(self) -> None:
        if self._handle:
            self._handle.delete()
            self._handle = None
            logger.debug("Porcupine handle released.")
