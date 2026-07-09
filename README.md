# ForReading Community Templates

Plantillas de la comunidad para usar con la extension [ForReading](https://readingisforyou.com).

## Que es esto?

La extension ForReading tiene soporte para dos tipos de proveedores TTS externos:

### Local providers

Sidecars que corren en tu propia maquina. Cualquier servidor HTTP con 3 endpoints funciona:

| Endpoint | Metodo | Respuesta |
|----------|--------|-----------|
| `/<name>/health` | GET | `{"ok":true, "voices_count":20}` |
| `/<name>/voices` | GET | `{"voices":[{"name":"zf_001","gender":"FEMALE"},...]}` |
| `/<name>/synthesize` | POST `{"text":"...","voice":"..."}` | audio/mpeg binario |

### Cloud providers

APIs externas (ElevenLabs, OpenAI, etc.). Se configuran desde **Opciones > Plantillas personalizadas** en la extension. El formato de cada template define:

- URL de sintesis
- URL de voces (opcional)
- Tipo de autenticacion
- Formato del body de la request
- Como parsear la respuesta

## Como usar

1. Descarga el template que quieras
2. **Local**: copia el `.json` a tu carpeta `server/`. Arranca con `launcher.bat`
3. **Cloud**: abre Opciones en la extension > **+ Anadir plantilla** > pega los campos del JSON

## Contribuir

1. Fork este repo
2. Crea tu template siguiendo `schema.json`
3. PR con descripcion clara

## Templates incluidos

### Local
| Template | Voces | GPU | Idiomas |
|----------|-------|-----|---------|
| [Kokoro](local/kokoro.json) | 50+ | Si | EN, ZH, JA, FR, KR |
| [Edge TTS](local/edge-tts.json) | 300+ | No | 100+ |
| [CosyVoice](local/cosyvoice.json) | 30+ | Si | ZH (principal) |

### Cloud
| Template | Free tier | Idiomas |
|----------|-----------|---------|
| [ElevenLabs](cloud/elevenlabs.json) | 10K/mes | 29 |
| [OpenAI TTS](cloud/openai-tts.json) | No | EN |
| [PlayHT](cloud/playht.json) | Si | 30+ |

## Licencia

MIT — usa, modifica, comparte.
