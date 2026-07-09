#!/usr/bin/env python3
"""
MINIMAL TTS Provider Template — start here to add your own TTS model.

This is the simplest possible HTTP server that works with ForReading.
It exposes 3 endpoints on a single port. The extension auto-discovers it.

HOW TO USE:
  1. Replace synthesize() with your model's inference code
  2. Edit VOICES to list your model's available voices
  3. Run: python my_tts_provider.py
  4. Open the extension → your provider appears automatically

The 3-endpoint protocol:
  GET  /<name>/health     → {"ok": true, "voices_count": N}
  GET  /<name>/voices     → {"voices": [{name, gender, languageCode, ...}]}
  POST /<name>/synthesize → {"text": "..."} → audio/wav binary

SETUP (pick one):
  pip install flask         # if you prefer Flask
  # or just use the built-in http.server (no extra deps) — shown below
"""

import http.server
import json
import io
import wave

# ── CONFIG: Change these ──────────────────────────────────────
PROVIDER_NAME = "mytts"          # lowercase, no spaces (used in URL path)
HOST = "127.0.0.1"
PORT = 5590                      # pick an unused port

# ── VOICES: List your model's voices ──────────────────────────
VOICES = [
    {"name": "voice_1", "gender": "FEMALE", "lang": "en-US", "desc": "MyTTS · F · English"},
    {"name": "voice_2", "gender": "MALE",   "lang": "en-US", "desc": "MyTTS · M · English"},
]
VOICE_NAMES = {v["name"] for v in VOICES}

# ── STATE ─────────────────────────────────────────────────────
ready = False


def init_model():
    """Load your TTS model here. Called once at startup."""
    global ready
    # TODO: load your model
    # from my_tts_library import MyTTSModel
    # model = MyTTSModel.load("path/to/model")
    ready = True
    print(f"[{PROVIDER_NAME}] Model loaded")


def synthesize(text, voice_name):
    """Convert text to audio. Return WAV bytes."""
    if not ready:
        raise RuntimeError("Model not loaded")
    if voice_name not in VOICE_NAMES:
        voice_name = VOICES[0]["name"]

    # TODO: your model inference here
    # audio = model.synthesize(text, voice=voice_name)
    # return audio_to_wav(audio)

    # Placeholder: generate 1 second of silence
    import struct
    sample_rate = 24000
    silence = struct.pack("<" + "h" * sample_rate, *([0] * sample_rate))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(silence)
    return buf.getvalue()


def voices_for_lang(lang_filter=None):
    """Return voice list, optionally filtered by language."""
    result = []
    for v in VOICES:
        if lang_filter and v["lang"] != lang_filter:
            continue
        result.append({
            "name": v["name"],
            "gender": v["gender"],
            "languageCode": v["lang"],
            "provider": PROVIDER_NAME,
            "premium": False,
            "style": PROVIDER_NAME,
            "description": v["desc"],
        })
    return result


# ── HTTP Server (no changes needed below) ─────────────────────
class TTSHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silent

    def _send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        health_path = f"/{PROVIDER_NAME}/health"
        voices_path = f"/{PROVIDER_NAME}/voices"

        if self.path == health_path:
            self._send_json(200, {
                "provider": PROVIDER_NAME,
                "ok": ready,
                "voices_count": len(VOICES),
            })
        elif self.path == voices_path:
            lang = None
            if "?" in self.path:
                from urllib.parse import urlparse, parse_qs
                params = parse_qs(urlparse(self.path).query)
                lang = params.get("lang", [None])[0]
            self._send_json(200, {"voices": voices_for_lang(lang)})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        synth_path = f"/{PROVIDER_NAME}/synthesize"
        if self.path == synth_path:
            try:
                body = self._read_body()
                text = (body.get("text") or "").strip()
                voice = body.get("voice") or VOICES[0]["name"]
                if not text:
                    return self._send_json(400, {"error": "empty text"})

                wav_data = synthesize(text, voice)
                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(len(wav_data)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(wav_data)
            except Exception as e:
                print(f"[{PROVIDER_NAME}] Error: {e}", flush=True)
                self._send_json(500, {"error": str(e)})
        else:
            self._send_json(404, {"error": "not found"})


def main():
    init_model()
    server = http.server.HTTPServer((HOST, PORT), TTSHandler)
    print(f"[{PROVIDER_NAME}] http://{HOST}:{PORT}/{PROVIDER_NAME}/health", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
