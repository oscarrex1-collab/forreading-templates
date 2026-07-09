# ForReading Community Templates

Community-contributed TTS templates for the [ForReading](https://readingisforyou.com) extension.

---

## What is this?

ForReading supports two types of external TTS providers:

### Local providers

Sidecars running on your own machine. Any HTTP server with 3 endpoints works:

| Endpoint | Method | Response |
|----------|--------|----------|
| `/<name>/health` | GET | `{"ok":true, "voices_count":20, "device":"cuda"}` |
| `/<name>/voices` | GET | `{"voices":[{"name":"zf_001","gender":"FEMALE"},...]}` |
| `/<name>/synthesize` | POST | `{"text":"...","voice":"..."}` → audio/mpeg |

### Cloud providers

External APIs (ElevenLabs, OpenAI, etc.). Configure via **Options → Custom Templates** in the extension.

## How to use

1. Browse [`local/`](local/) or [`cloud/`](cloud/)
2. **Local**: copy the `.json` to your `server/` folder. Start sidecars with `server/launcher.bat`
3. **Cloud**: open Options in the extension → **+ Add template** → paste the JSON fields

## Contributing

1. Fork this repo
2. Create your template following [`schema.json`](schema.json)
3. Open a PR with a clear description

## Templates (17)

### Local (9)
| Template | Voices | GPU | Best for |
|----------|--------|-----|----------|
| [Kokoro](local/kokoro.json) | 50+ | Yes | Neural quality, multilingual |
| [Edge TTS](local/edge-tts.json) | 300+ | No | Free, no GPU, 100+ languages |
| [CosyVoice](local/cosyvoice.json) | 30+ | Yes | Chinese voices with emotion |
| [F5-TTS](local/f5-tts.json) | ∞ | Yes | Zero-shot cloning (5s audio) |
| [GPT-SoVITS](local/gpt-sovits.json) | ∞ | Yes | Chinese voice cloning, #1 community |
| [XTTS](local/xtts.json) | ∞ | Yes | 17 languages, 6s cloning |
| [Piper TTS](local/piper.json) | 100+ | No | Ultra-lightweight, Raspberry Pi |
| [MeloTTS](local/melo-tts.json) | 20+ | No | Lightweight, 6 languages |
| [ChatTTS](local/chattts.json) | 10 | Yes | Natural-sounding dialogue |

### Cloud (8)
| Template | Free tier | Best for |
|----------|-----------|----------|
| [ElevenLabs](cloud/elevenlabs.json) | 10K/mo | Premium voices + cloning |
| [OpenAI TTS](cloud/openai-tts.json) | No | 6 ultra-natural voices |
| [PlayHT](cloud/playht.json) | Yes | 800+ voices, long-form |
| [Amazon Polly](cloud/amazon-polly.json) | 5M/mo | AWS, 60+ voices |
| [Murf AI](cloud/murf.json) | 10min/mo | Studio quality |
| [Deepgram](cloud/deepgram.json) | 500K/mo | Ultra-fast, streaming |
| [Cartesia](cloud/cartesia.json) | 100K/mo | Sub-100ms latency |
| [IBM Watson](cloud/ibm-watson.json) | 10K/mo | Enterprise, 30+ languages |

## Format

All templates follow [`schema.json`](schema.json). Two types:

- **`"type": "local"`** — requires `port` + `setup.commands`
- **`"type": "cloud"`** — requires `urls.synthesize`, `auth`, optionally `requestFormat.bodyTemplate`

## License

MIT — use, modify, share.

---

## Español / 中文

[README_es.md](README_es.md) | [README_zh.md](README_zh.md)
