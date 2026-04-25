import sys
import types
from types import SimpleNamespace

import numpy as np

from services import stt


def test_create_stt_service_returns_api_service(stt_config_api, audio_config, mocker) -> None:
    mocker.patch("services.stt.OpenAI")

    service = stt.create_stt_service(stt_config_api, audio_config)

    assert isinstance(service, stt.WhisperAPIService)


def test_create_stt_service_returns_local_service(stt_config_local, audio_config, mocker) -> None:
    fake_module = types.ModuleType("faster_whisper")
    fake_module.WhisperModel = mocker.Mock()
    mocker.patch.dict(sys.modules, {"faster_whisper": fake_module})

    service = stt.create_stt_service(stt_config_local, audio_config)

    assert isinstance(service, stt.WhisperLocalService)


def test_whisper_api_record_and_transcribe_returns_transcript(stt_config_api, audio_config, mocker) -> None:
    mock_client = mocker.Mock()
    mock_client.audio.transcriptions.create.return_value = SimpleNamespace(text=" hello world ")
    mocker.patch("services.stt.OpenAI", return_value=mock_client)

    service = stt.WhisperAPIService(stt_config_api, audio_config)
    mocker.patch.object(service._recorder, "record", return_value=np.array([[1], [2]], dtype=np.int16))

    transcript = service.record_and_transcribe()

    assert transcript == "hello world"


def test_whisper_api_record_and_transcribe_returns_empty_when_no_audio(stt_config_api, audio_config, mocker) -> None:
    mocker.patch("services.stt.OpenAI")
    service = stt.WhisperAPIService(stt_config_api, audio_config)
    mocker.patch.object(service._recorder, "record", return_value=None)

    transcript = service.record_and_transcribe()

    assert transcript == ""


def test_whisper_local_record_and_transcribe_returns_transcript(stt_config_local, audio_config, mocker) -> None:
    fake_model = mocker.Mock()
    fake_model.transcribe.return_value = ([SimpleNamespace(text="local "), SimpleNamespace(text="ok")], None)

    fake_module = types.ModuleType("faster_whisper")
    fake_module.WhisperModel = mocker.Mock(return_value=fake_model)
    mocker.patch.dict(sys.modules, {"faster_whisper": fake_module})

    service = stt.WhisperLocalService(stt_config_local, audio_config)
    mocker.patch.object(service._recorder, "record", return_value=np.array([[1], [2]], dtype=np.int16))

    transcript = service.record_and_transcribe()

    assert transcript == "local ok"
