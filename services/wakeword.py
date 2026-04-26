"""
services/wakeword.py — Wake word detection services.

Supports both Porcupine and OpenWakeWord backends.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import numpy as np
import pvporcupine
import sounddevice as sd

try:
    from openwakeword import Model
except ImportError:  # pragma: no cover - exercised in runtime envs without dependency
    Model = None  # type: ignore[assignment]

from config import AudioConfig, WakeWordConfig

logger = logging.getLogger(__name__)


class PorcupineWakeWordService:
    """
    Wraps Porcupine to provide continuous wake word listening.

    Usage:
        service = PorcupineWakeWordService(wakeword_cfg, audio_cfg)
        service.listen(on_detected=my_callback)
    """

    def __init__(self, wakeword_cfg: WakeWordConfig, audio_cfg: AudioConfig) -> None:
        self._wakeword_cfg = wakeword_cfg
        self._audio_cfg = audio_cfg
        self._handle: pvporcupine.Porcupine | None = None

    def _build_handle(self) -> pvporcupine.Porcupine:
        if self._wakeword_cfg.keyword_path:
            logger.info("Using custom keyword model: %s", self._wakeword_cfg.keyword_path)
            return pvporcupine.create(
                access_key=self._wakeword_cfg.porcupine_access_key,
                keyword_paths=[self._wakeword_cfg.keyword_path],
            )
        logger.info("Using built-in keyword: %s", self._wakeword_cfg.keyword)
        return pvporcupine.create(
            access_key=self._wakeword_cfg.porcupine_access_key,
            keywords=[self._wakeword_cfg.keyword],
        )

    def listen(self, on_detected: Callable[[], None], stop_event=None) -> None:
        """Block and listen for the wake word."""
        self._handle = self._build_handle()
        frame_length = self._handle.frame_length
        sample_rate = self._handle.sample_rate

        logger.info("Wake word service ready — listening for '%s'", self._wakeword_cfg.keyword)

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


class OpenWakeWordService:
    """Wake word service powered by openwakeword models."""

    def __init__(self, wakeword_cfg: WakeWordConfig, audio_cfg: AudioConfig) -> None:
        self._wakeword_cfg = wakeword_cfg
        self._audio_cfg = audio_cfg
        self._model: Model | None = None

    def _build_model(self):
        if Model is None:
            raise RuntimeError(
                "openwakeword is not installed. Install dependencies from requirements.txt."
            )

        if self._wakeword_cfg.oww_model_path:
            logger.info("Using custom OpenWakeWord model: %s", self._wakeword_cfg.oww_model_path)
            return Model(wakeword_models=[self._wakeword_cfg.oww_model_path])

        logger.info("Using built-in OpenWakeWord model: %s", self._wakeword_cfg.oww_model)
        return Model(wakeword_models=[self._wakeword_cfg.oww_model])

    def listen(self, on_detected: Callable[[], None], stop_event=None) -> None:
        """Block and listen for the wake word using OpenWakeWord."""
        self._model = self._build_model()
        sample_rate = self._audio_cfg.sample_rate
        frame_length = 1280

        logger.info(
            "Wake word service ready — listening for '%s' (threshold=%.2f)",
            self._wakeword_cfg.oww_model,
            self._wakeword_cfg.oww_threshold,
        )

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
                pcm_int16 = np.asarray(pcm).flatten().astype(np.int16)
                predictions = self._model.predict(pcm_int16)

                if not predictions:
                    continue

                top_score = max(predictions.values())
                if top_score > self._wakeword_cfg.oww_threshold:
                    logger.info("Wake word detected! confidence=%.3f", top_score)
                    on_detected()

    def cleanup(self) -> None:
        self._model = None
        logger.debug("OpenWakeWord model released.")


# Backward compatibility for existing imports.
WakeWordService = PorcupineWakeWordService


def create_wakeword_service(wakeword_cfg: WakeWordConfig, audio_cfg: AudioConfig):
    """Create a wake word service instance for the configured backend."""
    backend = wakeword_cfg.backend.lower()

    if backend == "porcupine":
        return PorcupineWakeWordService(wakeword_cfg, audio_cfg)
    if backend == "openwakeword":
        return OpenWakeWordService(wakeword_cfg, audio_cfg)

    raise ValueError(f"Unsupported wake word backend: {wakeword_cfg.backend}")
