# ForReading — Plantillas de la Comunidad

Plantillas TTS de la comunidad para la extension [ForReading](https://readingisforyou.com).

[English](README.md) | [中文](README_zh.md)

## Que es esto?

ForReading soporta dos tipos de proveedores TTS externos: locales (sidecar en tu PC) y cloud (APIs externas). Cada template es un JSON que sigue el [`schema.json`](schema.json).

### Local

Cualquier servidor HTTP con 3 endpoints:

| Endpoint | Metodo | Respuesta |
|----------|--------|-----------|
| `/<nombre>/health` | GET | `{"ok":true, "voices_count":20}` |
| `/<nombre>/voices` | GET | `{"voices":[...]}` |
| `/<nombre>/synthesize` | POST | audio/mpeg |

### Cloud

APIs externas (ElevenLabs, OpenAI, etc.). Configuralas en **Opciones > Plantillas personalizadas**.

## Como usar

1. Explora [`local/`](local/) o [`cloud/`](cloud/)
2. **Local**: copia el `.json` a `server/`. Arranca con `launcher.bat`
3. **Cloud**: Opciones > **+ Anadir plantilla** > completa los campos

## Templates (17)

| Tipo | Template | Voces | GPU | Ideal para |
|------|----------|-------|-----|------------|
| Local | Kokoro | 50+ | Si | Calidad neural multilengua |
| Local | Edge TTS | 300+ | No | Gratis, sin GPU |
| Local | CosyVoice | 30+ | Si | Voces chinas con expresion |
| Local | F5-TTS | ∞ | Si | Clonacion con 5s de audio |
| Local | GPT-SoVITS | ∞ | Si | #1 en comunidad china |
| Local | XTTS | ∞ | Si | 17 idiomas |
| Local | Piper | 100+ | No | Raspberry Pi |
| Local | MeloTTS | 20+ | No | Ligero, 6 idiomas |
| Local | ChatTTS | 10 | Si | Dialogo conversacional |
| Cloud | ElevenLabs | - | - | Premium + clonacion |
| Cloud | OpenAI | - | - | 6 voces ultra-naturales |
| Cloud | PlayHT | - | - | 800+ voces |
| Cloud | Amazon Polly | - | - | AWS, capa gratuita |
| Cloud | Murf | - | - | Calidad estudio |
| Cloud | Deepgram | - | - | Ultra-rapido |
| Cloud | Cartesia | - | - | Latencia <100ms |
| Cloud | IBM Watson | - | - | Enterprise |

## Licencia

MIT.
