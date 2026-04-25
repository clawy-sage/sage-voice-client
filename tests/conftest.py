import pytest

from config import AudioConfig, OpenClawConfig, PorcupineConfig, STTConfig, TTSConfig


@pytest.fixture
def porcupine_config() -> PorcupineConfig:
    return PorcupineConfig(
        access_key="pc-access-key",
        keyword="jarvis",
        keyword_path=None,
    )


@pytest.fixture
def stt_config_local() -> STTConfig:
    return STTConfig(
        backend="local",
        api_key="",
        model="whisper-1",
        local_model="base",
        local_device="cpu",
        local_compute_type="int8",
        silence_timeout=1.0,
        max_seconds=5.0,
    )


@pytest.fixture
def stt_config_api() -> STTConfig:
    return STTConfig(
        backend="api",
        api_key="openai-key",
        model="whisper-1",
        local_model="base",
        local_device="cpu",
        local_compute_type="int8",
        silence_timeout=1.0,
        max_seconds=5.0,
    )


@pytest.fixture
def openclaw_config() -> OpenClawConfig:
    return OpenClawConfig(
        base_url="http://localhost:9999",
        api_token="token-123",
        session="main",
    )


@pytest.fixture
def tts_config() -> TTSConfig:
    return TTSConfig(
        api_key="eleven-key",
        voice_id="voice-123",
        model="eleven_turbo_v2_5",
    )


@pytest.fixture
def audio_config() -> AudioConfig:
    return AudioConfig(
        input_device=1,
        output_device=2,
        sample_rate=16000,
    )


@pytest.fixture
def required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORCUPINE_ACCESS_KEY", "pc-access-key")
    monkeypatch.setenv("PORCUPINE_KEYWORD", "jarvis")
    monkeypatch.delenv("PORCUPINE_KEYWORD_PATH", raising=False)

    monkeypatch.setenv("STT_BACKEND", "local")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("WHISPER_MODEL", "whisper-1")
    monkeypatch.setenv("WHISPER_LOCAL_MODEL", "base")
    monkeypatch.setenv("WHISPER_LOCAL_DEVICE", "cpu")
    monkeypatch.setenv("WHISPER_LOCAL_COMPUTE_TYPE", "int8")
    monkeypatch.setenv("RECORDING_SILENCE_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("RECORDING_MAX_SECONDS", "30")

    monkeypatch.setenv("OPENCLAW_BASE_URL", "http://localhost:9999")
    monkeypatch.setenv("OPENCLAW_API_TOKEN", "token-123")
    monkeypatch.setenv("OPENCLAW_SESSION", "main")

    monkeypatch.setenv("ELEVENLABS_API_KEY", "eleven-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "voice-123")
    monkeypatch.setenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")

    monkeypatch.setenv("AUDIO_INPUT_DEVICE_INDEX", "1")
    monkeypatch.setenv("AUDIO_OUTPUT_DEVICE_INDEX", "2")
    monkeypatch.setenv("AUDIO_SAMPLE_RATE", "16000")
