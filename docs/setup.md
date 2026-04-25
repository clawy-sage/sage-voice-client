# Setup Guide

## Prerequisites

- Python 3.10 or newer
- A working microphone
- The following accounts/keys:
  - [Picovoice Console](https://console.picovoice.ai/) — free Porcupine access key
  - [OpenClaw](https://openclaw.ai/) — running locally or remotely
  - [ElevenLabs](https://elevenlabs.io/) — for TTS
  - [OpenAI](https://platform.openai.com/) — only if you use Whisper API backend (`STT_BACKEND=api`)

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

Open `.env` and fill in required values.

Always required:

| Variable | Description |
|---|---|
| `PORCUPINE_ACCESS_KEY` | From Picovoice Console |
| `OPENCLAW_API_TOKEN` | Your OpenClaw gateway token |
| `ELEVENLABS_API_KEY` | For TTS synthesis |

Conditionally required:

| Variable | When required |
|---|---|
| `OPENAI_API_KEY` | Only when `STT_BACKEND=api` |

---

## Local Whisper (offline, free)

Set this in `.env`:

```bash
STT_BACKEND=local
```

Why use `faster-whisper` locally:

- No API cost
- Fully offline transcription
- Typically faster than `openai-whisper` on the same machine

Model size trade-offs:

| Model | Approx. size | Speed | Accuracy |
|---|---:|---|---|
| `tiny` | ~75 MB | Fastest | Lowest |
| `base` | ~150 MB | Very fast | Good |
| `small` | ~500 MB | Fast | Better |
| `medium` | ~1.5 GB | Moderate | High |
| `large-v3` | ~3 GB | Slowest | Highest |

Notes:

- First run downloads the selected model and caches it at `~/.cache/huggingface/hub/`.
- `OPENAI_API_KEY` is not needed when `STT_BACKEND=local`.

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

## Performance Tuning

### Silence timeout trade-off (`RECORDING_SILENCE_TIMEOUT_SECONDS`)

This setting controls how quickly recording stops after you stop speaking:

- Lower values (e.g. `0.8`–`1.0`) → faster response, lower latency
- Higher values (e.g. `1.5`–`2.5`) → better at catching long pauses in speech

Recommended starting point for responsiveness: `1.0`.

### STT backend comparison (cost vs latency)

| Backend | Cost | Typical latency | Notes |
|---|---|---|---|
| `local` (faster-whisper) | Free | Low (after model warmup) | Best default for local/offline use |
| `api` (OpenAI Whisper) | Paid per usage | Medium (network + API) | Useful when local CPU/GPU is limited |

Tip: if your machine is modest, use `WHISPER_LOCAL_MODEL=tiny` or `base` for faster turn-around.

### TTS streaming playback

The client uses streaming TTS playback for faster perceived response:

- Audio starts playing as soon as enough streamed MP3 data is decoded
- Playback no longer waits for the entire response to synthesize first
- If streaming is unavailable, it automatically falls back to buffered playback

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
