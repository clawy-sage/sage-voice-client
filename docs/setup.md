# Setup Guide

## Prerequisites

- Python 3.10 or newer
- A working microphone
- The following accounts/keys:
  - [Picovoice Console](https://console.picovoice.ai/) — free Porcupine access key
  - [OpenAI](https://platform.openai.com/) — for Whisper STT
  - [OpenClaw](https://openclaw.ai/) — running locally or remotely
  - [ElevenLabs](https://elevenlabs.io/) — for TTS

---

## Step 1: Python environment

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 2: Configure .env

```bash
cp .env.example .env
```

Open `.env` and fill in all required values. Required fields:

| Variable | Description |
|---|---|
| `PORCUPINE_ACCESS_KEY` | From Picovoice Console |
| `OPENAI_API_KEY` | For Whisper transcription |
| `OPENCLAW_API_TOKEN` | Your OpenClaw gateway token |
| `ELEVENLABS_API_KEY` | For TTS synthesis |

---

## Step 3: Choose a wake word

**Built-in keywords** (no extra files needed):

- `jarvis`, `hey siri`, `alexa`, `computer`, `porcupine`, `bumblebee`, `picovoice`, `hey barista`, `americano`, `blueberry`, `grapefruit`, `grasshopper`, `hey google`, `ok google`, `terminator`

Set in `.env`:
```
PORCUPINE_KEYWORD=jarvis
```

**Custom wake word** (e.g. "Hey Sage"):  
Train one for free at [Picovoice Console](https://console.picovoice.ai/) → Wake Word → Custom.  
Download the `.ppn` file and set:
```
PORCUPINE_KEYWORD_PATH=/path/to/Hey-Sage_en_linux_v3_0_0.ppn
```

---

## Step 4: Find your audio device indices (optional)

If audio doesn't work with the default device:

```bash
python -c "from services.audio import AudioService; AudioService.list_devices()"
```

Set `AUDIO_INPUT_DEVICE_INDEX` and `AUDIO_OUTPUT_DEVICE_INDEX` in `.env` accordingly.

---

## Step 5: Run

```bash
python main.py
```

You should see:
```
00:00:01 [INFO] services.wakeword: Wake word service ready — listening for 'jarvis'
```

Say your wake word, then speak your message. The agent will respond through your speakers.

---

## Troubleshooting

**`EnvironmentError: Required environment variable ... is not set`**  
→ Check your `.env` file. Compare against `.env.example`.

**No audio / wrong microphone**  
→ Run `AudioService.list_devices()` and set the correct index.

**Porcupine `InvalidArgumentError`**  
→ Your access key is likely wrong or expired. Regenerate at [console.picovoice.ai](https://console.picovoice.ai/).

**OpenClaw returns empty reply**  
→ Verify `OPENCLAW_BASE_URL` and `OPENCLAW_API_TOKEN`. Test with:  
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:9999/api/status
```
