import numpy as np

from services.audio import AudioService


def test_audio_play_calls_sounddevice_play_and_wait(audio_config, mocker) -> None:
    mocker.patch("services.audio.sf.read", return_value=(np.zeros(8, dtype=np.float32), 16000))
    play_mock = mocker.patch("services.audio.sd.play")
    wait_mock = mocker.patch("services.audio.sd.wait")
    service = AudioService(audio_config)

    service.play(b"fake-bytes")

    assert play_mock.called and wait_mock.called


def test_audio_list_devices_calls_query_devices(mocker) -> None:
    query_mock = mocker.patch("services.audio.sd.query_devices", return_value=[{"name": "dev"}])

    AudioService.list_devices()

    assert query_mock.call_count == 1
