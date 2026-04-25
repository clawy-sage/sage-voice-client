import numpy as np

from config import PorcupineConfig
from services.wakeword import WakeWordService


def test_wakeword_uses_keyword_path_when_set(audio_config, mocker) -> None:
    cfg = PorcupineConfig(access_key="key", keyword="jarvis", keyword_path="/tmp/custom.ppn")
    create_mock = mocker.patch("services.wakeword.pvporcupine.create", return_value=mocker.Mock())
    service = WakeWordService(cfg, audio_config)

    service._build_handle()

    assert create_mock.call_args.kwargs["keyword_paths"] == ["/tmp/custom.ppn"]


def test_wakeword_uses_keyword_when_no_keyword_path(audio_config, mocker) -> None:
    cfg = PorcupineConfig(access_key="key", keyword="jarvis", keyword_path=None)
    create_mock = mocker.patch("services.wakeword.pvporcupine.create", return_value=mocker.Mock())
    service = WakeWordService(cfg, audio_config)

    service._build_handle()

    assert create_mock.call_args.kwargs["keywords"] == ["jarvis"]


def test_wakeword_cleanup_calls_delete(porcupine_config, audio_config, mocker) -> None:
    service = WakeWordService(porcupine_config, audio_config)
    handle = mocker.Mock()
    service._handle = handle

    service.cleanup()

    assert handle.delete.call_count == 1


def test_wakeword_on_detected_callback_called(audio_config, mocker) -> None:
    cfg = PorcupineConfig(access_key="key", keyword="jarvis", keyword_path=None)
    service = WakeWordService(cfg, audio_config)

    handle = mocker.Mock()
    handle.frame_length = 4
    handle.sample_rate = 16000
    handle.process.return_value = 0
    mocker.patch.object(service, "_build_handle", return_value=handle)

    stream = mocker.Mock()
    stream.read.return_value = (np.array([[1], [1], [1], [1]], dtype=np.int16), None)

    input_stream_cm = mocker.Mock()
    input_stream_cm.__enter__ = mocker.Mock(return_value=stream)
    input_stream_cm.__exit__ = mocker.Mock(return_value=False)
    mocker.patch("services.wakeword.sd.InputStream", return_value=input_stream_cm)

    stop_event = mocker.Mock()
    stop_event.is_set.side_effect = [False, True]
    on_detected = mocker.Mock()

    service.listen(on_detected=on_detected, stop_event=stop_event)

    assert on_detected.call_count == 1
