# sage-voice-client

A modular, wake-word-driven voice client for interacting with your OpenClaw agent via speech.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   sage-voice-client                  │
│                                                      │
│  ┌──────────┐   ┌──────────┐   ┌─────────────────┐  │
│  │ wakeword │──▶│   stt    │──▶│   openclaw_api  │  │
│  │ service  │   │ service  │   │     service     │  │
│  └──────────┘   └──────────┘   └────────┬────────┘  │
│                                         │            │
│                                ┌────────▼────────┐  │
│                                │   tts service   │  │
│                                └────────┬────────┘  │
│                                         │            │
│                                ┌────────▼────────┐  │
│                                │  audio playback │  │
│                                └─────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Services

| Service | Responsibility |
|---|---|
| `wakeword` | Listens continuously for the wake word using Porcupine |
| `stt` | Records audio after wake word and transcribes via OpenAI Whisper |
| `openclaw_api` | Sends transcript to OpenClaw and receives agent reply |
| `tts` | Converts agent reply to speech via ElevenLabs |
| `audio` | Plays back audio through the system speaker |

## Quickstart

```bash
# 1. Clone and enter
git clone https://github.com/YOUR_USERNAME/sage-voice-client
cd sage-voice-client

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your actual API keys

# 5. Run
python main.py
```

## Configuration

All configuration lives in `.env`. See `.env.example` for all available options.

## Requirements

- Python 3.10+
- A microphone connected to your PC
- Porcupine access key (free at [picovoice.io](https://picovoice.io))
- OpenAI API key (for Whisper STT)
- OpenClaw running locally or remotely
- ElevenLabs API key (for TTS)

## Project Structure

```
sage-voice-client/
├── main.py               # Entry point — orchestrates all services
├── .env.example          # Example environment config (no real keys)
├── requirements.txt      # Python dependencies
├── services/
│   ├── __init__.py
│   ├── wakeword.py       # Porcupine wake word detection
│   ├── stt.py            # Whisper speech-to-text
│   ├── openclaw_api.py   # OpenClaw agent API client
│   ├── tts.py            # ElevenLabs text-to-speech
│   └── audio.py          # Audio playback
├── config.py             # Typed config loader (reads from .env)
└── docs/
    └── setup.md          # Detailed setup guide
```

## License

MIT
