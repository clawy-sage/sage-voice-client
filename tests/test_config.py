import pytest

from config import AudioConfig, Config, STTConfig, WakeWordConfig


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


def test_wakeword_defaults_to_porcupine_when_legacy_key_is_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WAKEWORD_BACKEND", raising=False)
    monkeypatch.setenv("PORCUPINE_ACCESS_KEY", "pc-key")

    cfg = WakeWordConfig.from_env()

    assert cfg.backend == "porcupine"


def test_wakeword_defaults_to_openwakeword_without_backend_or_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WAKEWORD_BACKEND", raising=False)
    monkeypatch.delenv("PORCUPINE_ACCESS_KEY", raising=False)

    cfg = WakeWordConfig.from_env()

    assert cfg.backend == "openwakeword"


def test_wakeword_requires_porcupine_key_when_backend_is_porcupine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WAKEWORD_BACKEND", "porcupine")
    monkeypatch.delenv("PORCUPINE_ACCESS_KEY", raising=False)

    with pytest.raises(EnvironmentError):
        WakeWordConfig.from_env()
