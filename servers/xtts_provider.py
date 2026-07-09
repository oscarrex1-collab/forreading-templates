#!/usr/bin/env python3
"""
XTTS Provider — Coqui TTS with voice cloning for ForReading.
17 languages. Clone any voice from a 6-second audio sample.
GPU recommended (CUDA).

Setup: pip install TTS torch
First run auto-downloads the model (~2GB).
"""

import http.server
import json
import io
import wave
import time
import os
import numpy as np

HOST = '127.0.0.1'
PORT = 5527
MODEL_NAME = 'tts_models/multilingual/multi-dataset/xtts_v2'

# ── Built-in speaker voices for quick start ──
VOICES = [
    {'name': 'en_female_1', 'gender': 'FEMALE', 'lang': 'en', 'desc': 'XTTS · F · English (built-in)'},
    {'name': 'en_male_1', 'gender': 'MALE', 'lang': 'en', 'desc': 'XTTS · M · English (built-in)'},
    {'name': 'es_female_1', 'gender': 'FEMALE', 'lang': 'es', 'desc': 'XTTS · F · Spanish (built-in)'},
    {'name': 'fr_female_1', 'gender': 'FEMALE', 'lang': 'fr', 'desc': 'XTTS · F · French (built-in)'},
    {'name': 'de_female_1', 'gender': 'FEMALE', 'lang': 'de', 'desc': 'XTTS · F · German (built-in)'},
    {'name': 'it_female_1', 'gender': 'FEMALE', 'lang': 'it', 'desc': 'XTTS · F · Italian (built-in)'},
    {'name': 'pt_female_1', 'gender': 'FEMALE', 'lang': 'pt', 'desc': 'XTTS · F · Portuguese (built-in)'},
    {'name': 'pl_female_1', 'gender': 'FEMALE', 'lang': 'pl', 'desc': 'XTTS · F · Polish (built-in)'},
    {'name': 'zh_female_1', 'gender': 'FEMALE', 'lang': 'zh-cn', 'desc': 'XTTS · F · Chinese (built-in)'},
    {'name': 'ja_female_1', 'gender': 'FEMALE', 'lang': 'ja', 'desc': 'XTTS · F · Japanese (built-in)'},
    {'name': 'ko_female_1', 'gender': 'FEMALE', 'lang': 'ko', 'desc': 'XTTS · F · Korean (built-in)'},
    {'name': 'ar_female_1', 'gender': 'FEMALE', 'lang': 'ar', 'desc': 'XTTS · F · Arabic (built-in)'},
    {'name': 'tr_female_1', 'gender': 'FEMALE', 'lang': 'tr', 'desc': 'XTTS · F · Turkish (built-in)'},
    {'name': 'nl_female_1', 'gender': 'FEMALE', 'lang': 'nl', 'desc': 'XTTS · F · Dutch (built-in)'},
    {'name': 'cs_female_1', 'gender': 'FEMALE', 'lang': 'cs', 'desc': 'XTTS · F · Czech (built-in)'},
    {'name': 'ru_female_1', 'gender': 'FEMALE', 'lang': 'ru', 'desc': 'XTTS · F · Russian (built-in)'},
    {'name': 'hu_female_1', 'gender': 'FEMALE', 'lang': 'hu', 'desc': 'XTTS · F · Hungarian (built-in)'},
]

VOICE_NAMES = {v['name'] for v in VOICES}
tts_model = None
device = 'cpu'

def init_xtts():
    global tts_model, device
    import torch
    from TTS.api import TTS
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'[xtts] Loading {MODEL_NAME} on {device}...', flush=True)
    t0 = time.time()
    tts_model = TTS(model_name=MODEL_NAME, progress_bar=False).to(device)
    print(f'[xtts] Loaded in {time.time()-t0:.1f}s', flush=True)

def synthesize(text, voice_name):
    if tts_model is None:
        raise RuntimeError('XTTS not initialized')
    if voice_name not in VOICE_NAMES:
        voice_name = 'en_female_1'
    wav_np = tts_model.tts(text=text, speaker=voice_name, language=voice_name.split('_')[0])
    wav_np = np.array(wav_np)
    max_val = max(abs(wav_np).max(), 1e-8)
    audio_int16 = (wav_np / max_val * 32767).astype('int16')
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()

class XTTSHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def _check_origin(self):
        origin = self.headers.get('Origin', '')
        if not origin:
            return True
        if origin.startswith('chrome-extension://') or origin.startswith('moz-extension://'):
            return True
        self._send_json(403, {'error': 'origin not allowed'})
        return False

    def _send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length).decode('utf-8')) if length else {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if not self._check_origin(): return
        if self.path == '/xtts/health':
            self._send_json(200, {'provider': 'xtts', 'ok': tts_model is not None, 'voices_count': len(VOICES), 'device': device})
        elif self.path == '/xtts/voices':
            out = [{
                'name': v['name'], 'gender': v['gender'],
                'languageCode': v['lang'], 'provider': 'xtts',
                'premium': False, 'style': 'xtts', 'description': v['desc']
            } for v in VOICES]
            self._send_json(200, {'voices': out})
        else:
            self._send_json(404, {'error': 'not found'})

    def do_POST(self):
        if not self._check_origin(): return
        if self.path == '/xtts/synthesize':
            try:
                body = self._read_body()
                text = (body.get('text') or '').strip()
                voice = body.get('voice') or 'en_female_1'
                if not text:
                    return self._send_json(400, {'error': 'empty text'})
                wav = synthesize(text, voice)
                self.send_response(200)
                self.send_header('Content-Type', 'audio/wav')
                self.send_header('Content-Length', str(len(wav)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(wav)
            except Exception as e:
                print(f'[xtts] Error: {e}', flush=True)
                self._send_json(500, {'error': str(e)})
        else:
            self._send_json(404, {'error': 'not found'})

def main():
    init_xtts()
    print(f'[xtts] http://{HOST}:{PORT} — {len(VOICES)} voices, {device}', flush=True)
    server = http.server.HTTPServer((HOST, PORT), XTTSHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == '__main__':
    main()
