# ForReading Community Templates

Plantillas de la comunidad para usar con la extension [ForReading](https://readingisforyou.com).

## Que es esto?

La extension ForReading tiene soporte para dos tipos de proveedores TTS externos:

### Local providers

Sidecars que corren en tu propia maquina. Cualquier servidor HTTP con 3 endpoints funciona:

| Endpoint | Metodo | Respuesta |
|----------|--------|-----------|
| `/<name>/health` | GET | `{"ok":true, "voices_count":20, "device":"cuda"}` |
| `/<name>/voices` | GET | `{"voices":[{"name":"zf_001","gender":"FEMALE"},...]}` |
| `/<name>/synthesize` | POST | `{"text":"...","voice":"..."}` -> audio/mpeg |

### Cloud providers

APIs externas (ElevenLabs, OpenAI, etc.). Se configuran desde **Opciones > Plantillas personalizadas** en la extension.

## Como usar

1. Navega [`local/`](local/) o [`cloud/`](cloud/)
2. **Local**: copia el `.json` a tu carpeta `server/`. Arranca los sidecars con `server/launcher.bat`
3. **Cloud**: abre Opciones en la extension > **+ Anadir plantilla** > pega los campos del JSON

## Contribuir

1. Fork este repo
2. Crea tu template siguiendo [`schema.json`](schema.json)
3. PR con descripcion clara

## Templates incluidos (17)

### Local (9)
| Template | Voces | GPU | Destaca por |
|----------|-------|-----|-------------|
| [Kokoro](local/kokoro.json) | 50+ | Si | Calidad neural, multilengua |
| [Edge TTS](local/edge-tts.json) | 300+ | No | Gratis, sin GPU, 100+ idiomas |
| [CosyVoice](local/cosyvoice.json) | 30+ | Si | Voces chinas con emocion |
| [F5-TTS](local/f5-tts.json) | ∞ | Si | Clonacion zero-shot (5s audio) |
| [GPT-SoVITS](local/gpt-sovits.json) | ∞ | Si | Clonacion vocal china, #1 comunidad |
| [XTTS](local/xtts.json) | ∞ | Si | 17 idiomas, clonacion 6s |
| [Piper TTS](local/piper.json) | 100+ | No | Ultra-ligero, Raspberry Pi |
| [MeloTTS](local/melo-tts.json) | 20+ | No | Ligero, 6 idiomas |
| [ChatTTS](local/chattts.json) | 10 | Si | Conversacional natural |

### Cloud (8)
| Template | Free tier | Destaca por |
|----------|-----------|-------------|
| [ElevenLabs](cloud/elevenlabs.json) | 10K/mes | Voces premium + clonacion |
| [OpenAI TTS](cloud/openai-tts.json) | No | 6 voces ultra-naturales |
| [PlayHT](cloud/playht.json) | Si | 800+ voces, long-form |
| [Amazon Polly](cloud/amazon-polly.json) | 5M/mes | AWS, 60+ voces |
| [Murf AI](cloud/murf.json) | 10min/mes | Calidad estudio |
| [Deepgram](cloud/deepgram.json) | 500K/mes | Ultra-rapido, streaming |
| [Cartesia](cloud/cartesia.json) | 100K/mes | Latencia sub-100ms |
| [IBM Watson](cloud/ibm-watson.json) | 10K/mes | Enterprise, 30+ idiomas |

## Formato

Todos los templates siguen [`schema.json`](schema.json). Dos tipos:

- **`"type": "local"`** — require `port` y `setup.commands`
- **`"type": "cloud"`** — requiere `urls.synthesize`, `auth`, y opcionalmente `requestFormat.bodyTemplate`

## Licencia

MIT — usa, modifica, comparte.
