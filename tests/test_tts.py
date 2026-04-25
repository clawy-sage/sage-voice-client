from services.tts import TTSService


def test_tts_synthesize_returns_bytes(tts_config, mocker) -> None:
    mocker.patch("services.tts.ElevenLabs")
    service = TTSService(tts_config)
    mocker.patch.object(service, "_convert", return_value=[b"abc", b"123"])

    audio = service.synthesize("hello")

    assert audio == b"abc123"


def test_tts_synthesize_and_play_calls_audio_service(tts_config, mocker) -> None:
    mocker.patch("services.tts.ElevenLabs")
    service = TTSService(tts_config)
    mocker.patch.object(service, "_convert", side_effect=TypeError("no stream"))
    mocker.patch.object(service, "synthesize", return_value=b"audio-bytes")
    audio_service = mocker.Mock()

    service.synthesize_and_play("hello", audio_service)

    audio_service.play.assert_called_once_with(b"audio-bytes")


def test_tts_empty_text_does_not_crash(tts_config, mocker) -> None:
    mocker.patch("services.tts.ElevenLabs")
    service = TTSService(tts_config)
    mocker.patch.object(service, "_convert", return_value=[])

    audio = service.synthesize("")

    assert audio == b""
