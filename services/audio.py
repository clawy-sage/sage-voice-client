"""
services/audio.py — Audio playback service.

Plays audio bytes through the system speaker using sounddevice + soundfile,
and supports low-gap playback of pre-decoded PCM chunks.
"""

from __future__ import annotations

import io
import logging
import queue

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

    @property
    def sample_rate(self) -> int:
        """Configured output sample rate."""
        return self._cfg.sample_rate

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

    def play_stream(self, chunk_queue: "queue.Queue[np.ndarray | None]") -> None:
        """
        Play a stream of int16 PCM chunks with minimal gap.

        Expected queue format:
            - numpy arrays with dtype int16, shape (frames,) for mono
              or (frames, channels) for multi-channel
            - a final `None` sentinel to signal end-of-stream

        Args:
            chunk_queue: Queue containing PCM chunks and a terminating None.
        """
        first = chunk_queue.get()
        if first is None:
            logger.debug("Received empty PCM stream.")
            return

        first_chunk = np.asarray(first, dtype=np.int16)
        channels = 1 if first_chunk.ndim == 1 else int(first_chunk.shape[1])

        logger.info(
            "Starting streamed playback (%d Hz, %d channel(s)).",
            self._cfg.sample_rate,
            channels,
        )

        with sd.RawOutputStream(
            samplerate=self._cfg.sample_rate,
            channels=channels,
            dtype="int16",
            device=self._cfg.output_device,
        ) as stream:
            stream.write(np.ascontiguousarray(first_chunk).tobytes())

            while True:
                chunk = chunk_queue.get()
                if chunk is None:
                    break

                pcm = np.asarray(chunk, dtype=np.int16)
                stream.write(np.ascontiguousarray(pcm).tobytes())

        logger.debug("Streamed playback finished.")

    @staticmethod
    def list_devices() -> None:
        """Print all available audio devices to stdout. Useful for config."""
        print(sd.query_devices())
