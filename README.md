# 🎬 YouTube Automation Pipeline

> **100% free tools** — Script → Voice → Visuals → Edit → Upload → Automate

Fully automated YouTube video creation and publishing using:
- **Groq / Ollama Llama 3** — AI script generation (free)
- **Edge-TTS** — natural voiceover, 400+ voices, no API key needed
- **Pexels API** — royalty-free stock footage (free, 200 req/hr)
- **FFmpeg + MoviePy** — video assembly with auto-captions
- **Whisper** — AI subtitle generation (runs locally, free)
- **YouTube Data API v3** — upload & schedule (~6 uploads/day free)
- **GitHub Actions** — fully automated cron runs (2,000 free min/month)

---

## 📁 Project Structure

```
youtube-workflow/
├── src/
│   ├── pipeline.py          # Main orchestrator — run this
│   ├── script_generator.py  # Groq / Ollama script writer
│   ├── voiceover.py         # Edge-TTS audio generator
│   ├── visuals.py           # Pexels stock footage downloader
│   ├── video_editor.py      # FFmpeg + MoviePy assembler
│   └── uploader.py          # YouTube Data API v3 uploader
├── .github/
│   └── workflows/
│       └── pipeline.yml     # GitHub Actions cron automation
├── topics.json              # Auto-topic list for scheduled runs
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚡ Quick Start (Local)

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/youtube-workflow.git
cd youtube-workflow

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install FFmpeg

| OS | Command |
|----|---------|
| macOS | `brew install ffmpeg` |
| Ubuntu/Debian | `sudo apt install ffmpeg` |
| Windows | Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH |

### 3. Get your free API keys

| Service | Where | Free Tier |
|---------|-------|-----------|
| **Groq** | [console.groq.com](https://console.groq.com) | Generous free tier |
| **Pexels** | [pexels.com/api](https://www.pexels.com/api/) | 200 req/hour |
| **YouTube** | [console.cloud.google.com](https://console.cloud.google.com) | ~6 uploads/day |

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 5. Set up YouTube OAuth (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable **YouTube Data API v3**
3. Create credentials → **OAuth 2.0 Client ID** → Desktop App
4. Download JSON → save as `client_secrets.json` in project root
5. First run will open a browser for you to authorize — `token.json` is saved automatically

### 6. Run the pipeline

```bash
# Single video (publishes immediately)
python src/pipeline.py "10 Python tips for beginners"

# Schedule for a future time
python src/pipeline.py "10 Python tips" --schedule 2024-12-01T18:00:00Z

# Dry run — skips YouTube upload, saves video locally
python src/pipeline.py "10 Python tips" --dry-run
```

Output is saved to `output/YYYYMMDD_HHMMSS/final_video.mp4`.

---

## 🤖 GitHub Actions Automation

The pipeline runs automatically on a schedule — no server needed.

### Setup

1. Push this repo to GitHub

2. Add these **Repository Secrets** (Settings → Secrets → Actions):

   | Secret | Value |
   |--------|-------|
   | `GROQ_API_KEY` | Your Groq API key |
   | `PEXELS_API_KEY` | Your Pexels API key |
   | `YOUTUBE_TOKEN_JSON` | Contents of your `token.json` file |

3. That's it! The workflow runs **Mon / Wed / Fri at 10:00 UTC** and picks a random topic from `topics.json`.

### Manual trigger

Go to **Actions → YouTube Automation Pipeline → Run workflow** and type any topic.

### Change the schedule

Edit `.github/workflows/pipeline.yml`:
```yaml
schedule:
  - cron: "0 10 * * 1,3,5"   # Mon/Wed/Fri 10am UTC
```
Use [crontab.guru](https://crontab.guru) to build your cron expression.

---

## 🔧 Configuration

### Switch to local Ollama (no internet needed for scripting)

```bash
# Install Ollama: https://ollama.ai
ollama pull llama3

# In .env, remove GROQ_API_KEY or add:
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### Change voice

Edit `src/voiceover.py` — `DEFAULT_VOICE` constant:
```python
DEFAULT_VOICE = "en-GB-SoniaNeural"   # British female
# DEFAULT_VOICE = "en-US-GuyNeural"   # US male
```

List all available voices:
```bash
edge-tts --list-voices
```

### Add your own topics

Edit `topics.json` — add as many as you like. Scheduled runs pick randomly.

---

## 🆓 Free Tier Summary

| Tool | Free Limit | Paid needed? |
|------|-----------|-------------|
| Groq API | ~14,400 tokens/min | ❌ Never |
| Edge-TTS | Unlimited | ❌ Never |
| Pexels API | 200 req/hour | ❌ Never |
| Whisper (local) | Unlimited | ❌ Never |
| FFmpeg | Unlimited | ❌ Never |
| YouTube API | ~6 uploads/day | ❌ Never |
| GitHub Actions | 2,000 min/month | ❌ Never |

**Total cost: $0/month** for up to ~3 videos/week.

---

## 🐛 Troubleshooting

**`PEXELS_API_KEY not set`** — Make sure `.env` is filled in and you ran `source .venv/bin/activate`.

**`FFmpeg not found`** — Install FFmpeg and ensure it's on your PATH (`ffmpeg -version`).

**YouTube auth loop** — Delete `token.json` and re-run to re-authorize.

**Whisper slow on first run** — It downloads the model (~150 MB) once. Subsequent runs are fast.

**GitHub Actions timeout** — Increase `timeout-minutes` in `pipeline.yml` if Whisper transcription is slow.

---

## 📄 License

MIT — use freely, star if useful ⭐
