"""
services/tts.py — Text-to-speech service via ElevenLabs.

Supports both buffered synthesis (backwards compatible) and perceived-streaming
playback by decoding incoming MP3 chunks and feeding PCM to AudioService.
"""

from __future__ import annotations

import io
import logging
import queue
import threading
from collections.abc import Iterable
from typing import TYPE_CHECKING

import numpy as np
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment

from config import TTSConfig

if TYPE_CHECKING:
    from services.audio import AudioService

logger = logging.getLogger(__name__)


class TTSService:
    """Wraps the ElevenLabs API to synthesize and/or play speech."""

    def __init__(self, cfg: TTSConfig) -> None:
        self._cfg = cfg
        self._client = ElevenLabs(api_key=cfg.api_key)

    def _convert(self, text: str, *, stream: bool) -> Iterable[bytes]:
        """Call ElevenLabs convert API with optional streaming."""
        kwargs = dict(
            voice_id=self._cfg.voice_id,
            text=text,
            model_id=self._cfg.model,
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            ),
        )

        if stream:
            kwargs["stream"] = True

        return self._client.text_to_speech.convert(**kwargs)

    def synthesize(self, text: str) -> bytes:
        """
        Convert text to complete MP3 bytes (buffered mode, backwards compat).
        """
        logger.info("Synthesizing buffered TTS for %d chars…", len(text))

        audio_stream = self._convert(text, stream=False)
        audio_bytes = b"".join(audio_stream)

        logger.debug("TTS produced %d bytes.", len(audio_bytes))
        return audio_bytes

    def synthesize_and_play(self, text: str, audio_service: "AudioService") -> None:
        """
        Stream TTS with early playback.

        Flow:
            1) Receive MP3 byte chunks from ElevenLabs
            2) Decode progressively with pydub as data accumulates
            3) Push int16 PCM chunks to AudioService.play_stream

        Falls back to buffered synthesize()+play() if streaming is unavailable.
        """
        logger.info("Synthesizing streaming TTS for %d chars…", len(text))

        compressed_q: "queue.Queue[bytes | None]" = queue.Queue(maxsize=64)
        pcm_q: "queue.Queue[np.ndarray | None]" = queue.Queue(maxsize=128)

        playback_thread = threading.Thread(
            target=audio_service.play_stream,
            args=(pcm_q,),
            daemon=True,
        )

        def decode_worker() -> None:
            buffer = bytearray()
            played_ms = 0
            stream_ended = False

            while True:
                chunk = compressed_q.get()
                if chunk is None:
                    stream_ended = True
                else:
                    buffer.extend(chunk)

                # Decode only when enough data is present, or on final flush.
                if not stream_ended and len(buffer) < 8192:
                    continue

                try:
                    segment = AudioSegment.from_file(io.BytesIO(bytes(buffer)), format="mp3")
                except Exception:
                    # Common early in stream: partial MP3 frames are not decodable yet.
                    if stream_ended:
                        logger.warning("Could not decode final MP3 stream chunk.")
                        break
                    continue

                if segment.frame_rate != audio_service.sample_rate:
                    segment = segment.set_frame_rate(audio_service.sample_rate)

                duration_ms = len(segment)
                if duration_ms <= played_ms:
                    if stream_ended:
                        break
                    continue

                new_audio = segment[played_ms:duration_ms]
                played_ms = duration_ms

                samples = np.array(new_audio.get_array_of_samples(), dtype=np.int16)
                if new_audio.channels > 1:
                    samples = samples.reshape((-1, new_audio.channels))

                frame_block = 2048
                for start in range(0, len(samples), frame_block):
                    pcm_q.put(samples[start : start + frame_block])

                if stream_ended:
                    break

            pcm_q.put(None)

        decode_thread = threading.Thread(target=decode_worker, daemon=True)

        try:
            try:
                audio_stream = self._convert(text, stream=True)
            except TypeError:
                logger.info("SDK does not support stream=True; falling back to buffered TTS.")
                audio_service.play(self.synthesize(text))
                return

            playback_thread.start()
            decode_thread.start()

            for chunk in audio_stream:
                if chunk:
                    compressed_q.put(chunk)

            compressed_q.put(None)
            decode_thread.join()
            playback_thread.join()

        except Exception as exc:
            logger.warning("Streaming TTS failed (%s); falling back to buffered mode.", exc)
            # Ensure any started threads can terminate cleanly.
            try:
                compressed_q.put(None)
                pcm_q.put(None)
            except Exception:
                pass
            audio_service.play(self.synthesize(text))
