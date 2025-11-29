<h1 align="center">🎬 context-aware-srt-translation 🎬</h1>
<h3 align="center">Stop translating subtitles line by line. Start shipping natural translations.</h3>

<p align="center">
  <strong>
    <em>The smarter subtitle translator. It reads your SRT, groups sequential lines for context, and uses GPT to produce translations that actually sound human.</em>
  </strong>
</p>

<p align="center">
  <a href="#"><img alt="python" src="https://img.shields.io/badge/python-3.10+-4D87E6.svg?style=flat-square"></a>
  <a href="#"><img alt="fastapi" src="https://img.shields.io/badge/FastAPI-0.109+-009688.svg?style=flat-square"></a>
  &nbsp;&nbsp;•&nbsp;&nbsp;
  <a href="#"><img alt="license" src="https://img.shields.io/badge/License-MIT-F9A825.svg?style=flat-square"></a>
  <a href="#"><img alt="platform" src="https://img.shields.io/badge/platform-macOS_|_Linux_|_Windows-2ED573.svg?style=flat-square"></a>
</p>

<p align="center">
  <img alt="context window" src="https://img.shields.io/badge/🧠_context_window-groups_3_lines_at_once-2ED573.svg?style=for-the-badge">
  <img alt="auto fallback" src="https://img.shields.io/badge/🔄_auto_fallback-OpenAI_→_DeepL-2ED573.svg?style=for-the-badge">
</p>

<div align="center">

### 🧭 Quick Navigation

[**⚡ Get Started**](#-get-started-in-60-seconds) •
[**✨ How It Works**](#-how-context-windows-work) •
[**🎮 API Usage**](#-api-usage) •
[**⚙️ Configuration**](#️-configuration) •
[**🆚 Why This Slaps**](#-why-this-slaps-other-methods)

</div>

---

**context-aware-srt-translation** is the translator your subtitles deserve. Stop feeding GPT one line at a time and getting robotic, disconnected results. This service groups sequential subtitle lines together, giving the AI the context it needs to understand the conversation and produce translations that actually flow naturally.

<div align="center">
<table>
<tr>
<td align="center">
<h3>🧠</h3>
<b>Context Windows</b><br/>
<sub>3 lines translated together</sub>
</td>
<td align="center">
<h3>⚡</h3>
<b>Concurrent Processing</b><br/>
<sub>Parallel chunk translation</sub>
</td>
<td align="center">
<h3>🔄</h3>
<b>Auto Fallback</b><br/>
<sub>OpenAI → DeepL seamlessly</sub>
</td>
</tr>
</table>
</div>

How it works:
- **You:** POST your SRT file to the API
- **Service:** Groups lines into context windows, translates concurrently
- **Result:** Natural translations that respect conversational flow
- **Bonus:** Full statistics on what happened

---

## 💥 Why This Slaps Other Methods

Line-by-line translation is a vibe-killer. Context windows make other methods look ancient.

<table align="center">
<tr>
<td align="center"><b>❌ Line-by-Line (Pain)</b></td>
<td align="center"><b>✅ Context Windows (Glory)</b></td>
</tr>
<tr>
<td>
<pre>
"I think we should..."  →  "Sanırım biz..."
"...go there tomorrow"  →  "...yarın oraya git"
</pre>
<sub>Disconnected. Robotic. Wrong verb forms.</sub>
</td>
<td>
<pre>
["I think we should...",
 "...go there tomorrow"]  →  
["Bence yarın oraya...",
 "...gitmeliyiz"]
</pre>
<sub>Connected. Natural. Correct grammar.</sub>
</td>
</tr>
</table>

The difference is **context**. When GPT sees the full thought, it understands the sentence structure, maintains speaker tone, and produces translations humans would actually write.

---

## 🚀 Get Started in 60 Seconds

### 1. Clone & Install

```bash
git clone https://github.com/yigitkonur/context-aware-srt-translation-gpt.git
cd context-aware-srt-translation-gpt
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Add your OpenAI API key (required)
# Add DeepL API key (optional fallback)
```

### 3. Run

```bash
python run.py
```

The API is now live at `http://localhost:8000` 🎉

---

## 🧠 How Context Windows Work

Instead of translating each subtitle line individually (which loses context), this service groups sequential lines:

```
┌─────────────────────────────────────────────────┐
│  Traditional: Line 1 → Translate → Output 1    │
│               Line 2 → Translate → Output 2    │
│               Line 3 → Translate → Output 3    │
│               ❌ No context between lines       │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  Context Window:                                │
│  [Line 1, Line 2, Line 3] → Translate Together  │
│               ↓                                 │
│  [Output 1, Output 2, Output 3]                 │
│               ✅ AI sees the full picture       │
└─────────────────────────────────────────────────┘
```

This allows GPT to:
- **Maintain speaker continuity** — Same character, same voice
- **Preserve conversation flow** — Questions match answers
- **Handle split sentences** — "I think..." + "...we should go" = coherent thought
- **Respect cultural context** — Idioms translated appropriately

---

## 🎮 API Usage

### Translate Subtitles

```bash
curl -X POST "http://localhost:8000/subtitle-translate" \
  -H "Content-Type: application/json" \
  -d '{
    "srt_content": "1\n00:00:01,000 --> 00:00:04,000\nHello, how are you?\n\n2\n00:00:05,000 --> 00:00:08,000\nI am doing great, thanks!",
    "source_language": "en",
    "target_language": "tr"
  }'
```

### Response

```json
{
  "translated_srt_content": "1\n00:00:01,000 --> 00:00:04,000\nMerhaba, nasılsın?\n\n2\n00:00:05,000 --> 00:00:08,000\nÇok iyiyim, teşekkürler!",
  "status": "success",
  "error_message": null,
  "stats": {
    "total_sentences": 2,
    "translated_sentences": 2,
    "failed_sentences": 0,
    "success_rate": 100.0,
    "openai_calls": 1,
    "deepl_calls": 0,
    "elapsed_seconds": 1.23
  }
}
```

### Health Check

```bash
curl http://localhost:8000/health
# {"status": "healthy", "version": "2.0.0"}
```

---

## ⚙️ Configuration

All settings via environment variables:

| Variable | Default | Description |
|:---------|:--------|:------------|
| `OPENAI_API_KEY` | — | **Required.** Your OpenAI API key |
| `DEEPL_API_KEY` | — | Optional fallback service |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for translations |
| `OPENAI_TEMPERATURE` | `0.3` | Lower = more consistent |
| `CONTEXT_WINDOW_SIZE` | `3` | Lines per translation chunk |
| `MAX_CONCURRENT_REQUESTS` | `10` | Parallel API calls |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## 📁 Project Structure

```
src/
├── config.py              # Environment configuration
├── models.py              # Pydantic request/response models
├── srt_parser.py          # SRT parsing & reconstruction
├── translator.py          # Main orchestration logic
├── main.py                # FastAPI application
└── services/
    ├── base.py            # Service interface
    ├── openai_service.py  # OpenAI implementation
    └── deepl_service.py   # DeepL fallback
```

---

## 🔥 API Documentation

Interactive docs available when running:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🛠️ Development

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run with hot reload
python run.py
```

---

## 🔥 Common Issues

| Problem | Solution |
|:--------|:---------|
| **OpenAI rate limit** | Reduce `MAX_CONCURRENT_REQUESTS` |
| **DeepL not working** | Check `DEEPL_API_KEY` is set correctly |
| **Translations cut off** | Increase `OPENAI_MAX_TOKENS` |
| **Wrong language codes** | Use ISO 639-1 codes: `en`, `tr`, `de`, `fr`, etc. |

---

<div align="center">

**Built with 🔥 because line-by-line subtitle translation is a crime against cinema.**

MIT © [Yiğit Konur](https://github.com/yigitkonur)

</div>
