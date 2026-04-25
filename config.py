"""
config.py — Typed configuration loader.

Reads all settings from environment variables (populated via .env).
Raises clear errors on startup if required values are missing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"See .env.example for setup instructions."
        )
    return value


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass(frozen=True)
class PorcupineConfig:
    access_key: str
    keyword: str
    keyword_path: str | None  # Path to custom .ppn file (overrides keyword)

    @classmethod
    def from_env(cls) -> "PorcupineConfig":
        return cls(
            access_key=_require("PORCUPINE_ACCESS_KEY"),
            keyword=_optional("PORCUPINE_KEYWORD", "jarvis"),
            keyword_path=_optional("PORCUPINE_KEYWORD_PATH") or None,
        )


@dataclass(frozen=True)
class STTConfig:
    backend: str
    api_key: str
    model: str
    local_model: str
    local_device: str
    local_compute_type: str
    silence_timeout: float
    max_seconds: float

    @classmethod
    def from_env(cls) -> "STTConfig":
        backend = _optional("STT_BACKEND", "local").lower()
        api_key = _require("OPENAI_API_KEY") if backend == "api" else _optional("OPENAI_API_KEY")

        return cls(
            backend=backend,
            api_key=api_key,
            model=_optional("WHISPER_MODEL", "whisper-1"),
            local_model=_optional("WHISPER_LOCAL_MODEL", "base"),
            local_device=_optional("WHISPER_LOCAL_DEVICE", "cpu"),
            local_compute_type=_optional("WHISPER_LOCAL_COMPUTE_TYPE", "int8"),
            silence_timeout=float(_optional("RECORDING_SILENCE_TIMEOUT_SECONDS", "1.0")),
            max_seconds=float(_optional("RECORDING_MAX_SECONDS", "30")),
        )


@dataclass(frozen=True)
class OpenClawConfig:
    base_url: str
    api_token: str
    session: str

    @classmethod
    def from_env(cls) -> "OpenClawConfig":
        return cls(
            base_url=_optional("OPENCLAW_BASE_URL", "http://localhost:9999"),
            api_token=_require("OPENCLAW_API_TOKEN"),
            session=_optional("OPENCLAW_SESSION", "main"),
        )


@dataclass(frozen=True)
class TTSConfig:
    api_key: str
    voice_id: str
    model: str

    @classmethod
    def from_env(cls) -> "TTSConfig":
        return cls(
            api_key=_require("ELEVENLABS_API_KEY"),
            voice_id=_optional("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL"),
            model=_optional("ELEVENLABS_MODEL", "eleven_turbo_v2_5"),
        )


@dataclass(frozen=True)
class AudioConfig:
    input_device: int | None
    output_device: int | None
    sample_rate: int

    @classmethod
    def from_env(cls) -> "AudioConfig":
        raw_in = _optional("AUDIO_INPUT_DEVICE_INDEX")
        raw_out = _optional("AUDIO_OUTPUT_DEVICE_INDEX")
        return cls(
            input_device=int(raw_in) if raw_in else None,
            output_device=int(raw_out) if raw_out else None,
            sample_rate=int(_optional("AUDIO_SAMPLE_RATE", "16000")),
        )


@dataclass(frozen=True)
class Config:
    porcupine: PorcupineConfig
    stt: STTConfig
    openclaw: OpenClawConfig
    tts: TTSConfig
    audio: AudioConfig

    @classmethod
    def load(cls) -> "Config":
        return cls(
            porcupine=PorcupineConfig.from_env(),
            stt=STTConfig.from_env(),
            openclaw=OpenClawConfig.from_env(),
            tts=TTSConfig.from_env(),
            audio=AudioConfig.from_env(),
        )
