"""
services/tts.py — Text-to-speech service via ElevenLabs.

Converts a text string to raw PCM/MP3 audio bytes.
"""

from __future__ import annotations

import logging

from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

from config import TTSConfig

logger = logging.getLogger(__name__)


class TTSService:
    """
    Wraps the ElevenLabs API to synthesize speech.

    Usage:
        svc = TTSService(tts_cfg)
        audio_bytes = svc.synthesize("Hello, how can I help?")
    """

    def __init__(self, cfg: TTSConfig) -> None:
        self._cfg = cfg
        self._client = ElevenLabs(api_key=cfg.api_key)

    def synthesize(self, text: str) -> bytes:
        """
        Convert text to audio bytes (mp3).

        Args:
            text: The text to speak.

        Returns:
            Raw audio bytes (MP3 format).
        """
        logger.info("Synthesizing TTS for %d chars…", len(text))

        audio_stream = self._client.text_to_speech.convert(
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

        audio_bytes = b"".join(audio_stream)
        logger.debug("TTS produced %d bytes.", len(audio_bytes))
        return audio_bytes
