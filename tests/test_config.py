import pytest

from config import AudioConfig, Config, STTConfig


def test_config_load_succeeds_with_required_env(required_env) -> None:
    cfg = Config.load()

    assert cfg.openclaw.api_token == "token-123"


def test_config_load_raises_when_required_var_missing(required_env, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENCLAW_API_TOKEN", raising=False)

    with pytest.raises(EnvironmentError):
        Config.load()


def test_stt_config_default_backend_is_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("STT_BACKEND", raising=False)

    cfg = STTConfig.from_env()

    assert cfg.backend == "local"


def test_stt_config_requires_openai_key_only_for_api_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STT_BACKEND", "api")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(EnvironmentError):
        STTConfig.from_env()


def test_audio_config_parses_device_indices(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUDIO_INPUT_DEVICE_INDEX", "4")
    monkeypatch.delenv("AUDIO_OUTPUT_DEVICE_INDEX", raising=False)

    cfg = AudioConfig.from_env()

    assert (cfg.input_device, cfg.output_device) == (4, None)
