"""
main.py — sage-voice-client entry point.

Orchestrates all services in a simple wake-word → STT → agent → TTS loop.

Flow:
    1. WakeWordService listens for the configured wake word
    2. On detection: STTService records and transcribes the utterance
    3. OpenClawService sends the transcript to the agent
    4. TTSService converts the reply to speech
    5. AudioService plays the response
    6. Return to step 1
"""

from __future__ import annotations

import logging
import sys
import threading

from config import Config
from services.wakeword import WakeWordService
from services.stt import STTService
from services.openclaw_api import OpenClawService
from services.tts import TTSService
from services.audio import AudioService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting sage-voice-client…")

    try:
        cfg = Config.load()
    except EnvironmentError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)

    stt_service = STTService(cfg.stt, cfg.audio)
    openclaw_service = OpenClawService(cfg.openclaw)
    tts_service = TTSService(cfg.tts)
    audio_service = AudioService(cfg.audio)
    wake_service = WakeWordService(cfg.porcupine, cfg.audio)

    # Mutex to prevent concurrent pipeline runs
    # (if wake word fires again while still processing)
    _processing = threading.Lock()

    def on_wake_word() -> None:
        if not _processing.acquire(blocking=False):
            logger.debug("Already processing — ignoring duplicate wake word.")
            return

        try:
            transcript = stt_service.record_and_transcribe()
            if not transcript:
                logger.info("Nothing transcribed — going back to listening.")
                return

            reply = openclaw_service.send(transcript)
            if not reply:
                logger.info("Empty agent reply.")
                return

            audio_bytes = tts_service.synthesize(reply)
            audio_service.play(audio_bytes)

        except Exception as exc:
            logger.exception("Pipeline error: %s", exc)
        finally:
            _processing.release()

    stop_event = threading.Event()

    try:
        wake_service.listen(on_detected=on_wake_word, stop_event=stop_event)
    except KeyboardInterrupt:
        logger.info("Interrupted — shutting down.")
    finally:
        stop_event.set()
        wake_service.cleanup()
        openclaw_service.close()
        logger.info("Goodbye.")


if __name__ == "__main__":
    main()
