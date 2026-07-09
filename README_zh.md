# ForReading 社区模板

[ForReading](https://readingisforyou.com) 扩展的社区 TTS 模板。

[English](README.md) | [Español](README_es.md)

## 这是什么？

ForReading 支持两种外部 TTS 提供商：本地侧车（运行在你自己的电脑上）和云端 API。每个模板都是一个遵循 [`schema.json`](schema.json) 的 JSON 文件。

### 本地提供商

任何具有以下 3 个端点的 HTTP 服务器：

| 端点 | 方法 | 响应 |
|----------|--------|----------|
| `/<name>/health` | GET | `{"ok":true, "voices_count":20}` |
| `/<name>/voices` | GET | `{"voices":[...]}` |
| `/<name>/synthesize` | POST | audio/mpeg |

### 云端提供商

外部 API（ElevenLabs、OpenAI 等）。在扩展的 **选项 > 自定义模板** 中配置。

## 使用方法

1. 浏览 [`local/`](local/) 或 [`cloud/`](cloud/)
2. **本地**：将 `.json` 复制到 `server/` 文件夹。用 `launcher.bat` 启动
3. **云端**：选项 > **+ 添加模板** > 填写 JSON 字段

## 模板 (17)

| 类型 | 模板 | 音色 | GPU | 最适合 |
|------|----------|-------|-----|------------|
| 本地 | Kokoro | 50+ | 是 | 神经质量，多语言 |
| 本地 | Edge TTS | 300+ | 否 | 免费，无需 GPU |
| 本地 | CosyVoice | 30+ | 是 | 中文情感语音 |
| 本地 | F5-TTS | ∞ | 是 | 5秒音频零-shot克隆 |
| 本地 | GPT-SoVITS | ∞ | 是 | 中文声音克隆，社区#1 |
| 本地 | XTTS | ∞ | 是 | 17种语言 |
| 本地 | Piper | 100+ | 否 | 树莓派 |
| 本地 | MeloTTS | 20+ | 否 | 轻量，6种语言 |
| 本地 | ChatTTS | 10 | 是 | 自然对话 |
| 云端 | ElevenLabs | - | - | 高级+克隆 |
| 云端 | OpenAI | - | - | 6种超自然音色 |
| 云端 | PlayHT | - | - | 800+音色 |
| 云端 | Amazon Polly | - | - | AWS免费套餐 |
| 云端 | Murf | - | - | 录音室品质 |
| 云端 | Deepgram | - | - | 超快速度 |
| 云端 | Cartesia | - | - | 低于100ms延迟 |
| 云端 | IBM Watson | - | - | 企业级 |

## 许可证

MIT.
