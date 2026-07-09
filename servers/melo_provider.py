#!/usr/bin/env python3
"""
MeloTTS Provider — lightweight multilingual TTS for ForReading.
Supports EN, ZH, JA, KR, FR, ES. CPU-friendly, decent quality.

Setup: pip install melo-tts torch
"""

import http.server
import json
import io
import wave
import time
import numpy as np

HOST = '127.0.0.1'
PORT = 5526

VOICES = [
    {'name': 'EN-US', 'gender': 'FEMALE', 'lang': 'en-US', 'desc': 'MeloTTS · F · English (US)'},
    {'name': 'EN-BR', 'gender': 'FEMALE', 'lang': 'en-GB', 'desc': 'MeloTTS · F · English (UK)'},
    {'name': 'EN-AU', 'gender': 'FEMALE', 'lang': 'en-AU', 'desc': 'MeloTTS · F · English (AU)'},
    {'name': 'EN-NG', 'gender': 'MALE',   'lang': 'en-US', 'desc': 'MeloTTS · M · English (NG)'},
    {'name': 'ZH', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'MeloTTS · F · Chinese'},
    {'name': 'ZH-MIX', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'MeloTTS · F · Chinese (mixed)'},
    {'name': 'JA', 'gender': 'FEMALE', 'lang': 'ja-JP', 'desc': 'MeloTTS · F · Japanese'},
    {'name': 'KR', 'gender': 'FEMALE', 'lang': 'ko-KR', 'desc': 'MeloTTS · F · Korean'},
    {'name': 'FR', 'gender': 'FEMALE', 'lang': 'fr-FR', 'desc': 'MeloTTS · F · French'},
    {'name': 'ES', 'gender': 'FEMALE', 'lang': 'es-ES', 'desc': 'MeloTTS · F · Spanish'},
]

VOICE_NAMES = {v['name'] for v in VOICES}
model = None
device = 'cpu'

def init_melo():
    global model, device
    import torch
    from melo.api import TTS
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'[melo] Loading on {device}...', flush=True)
    t0 = time.time()
    model = TTS(language='EN', device=device)
    print(f'[melo] Loaded in {time.time()-t0:.1f}s', flush=True)

def lang_for_voice(name):
    return name.split('-')[0]

def synthesize(text, voice_name):
    if model is None:
        raise RuntimeError('MeloTTS not initialized')
    if voice_name not in VOICE_NAMES:
        voice_name = 'EN-US'
    lang = lang_for_voice(voice_name)
    if lang != model.language:
        from melo.api import TTS
        global model
        model = TTS(language=lang, device=device)
    
    audio_np = model.tts_to_file(text, model.hps.data.spk2id[voice_name], quiet=True)
    if audio_np is None:
        audio_np = model.tts_to_file(text, 0, quiet=True)
    if audio_np is None:
        raise RuntimeError('Synthesis returned None')
    
    audio_np = np.array(audio_np)
    max_val = max(abs(audio_np).max(), 1e-8)
    audio_int16 = (audio_np / max_val * 32767).astype('int16')
    
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(model.hps.data.sampling_rate)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()

class MeloHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

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
        if self.path == '/melo/health':
            self._send_json(200, {'provider': 'melo', 'ok': model is not None, 'voices_count': len(VOICES), 'device': device})
        elif self.path == '/melo/voices':
            out = [{
                'name': v['name'], 'gender': v['gender'],
                'languageCode': v['lang'], 'provider': 'melo',
                'premium': False, 'style': 'melo', 'description': v['desc']
            } for v in VOICES]
            self._send_json(200, {'voices': out})
        else:
            self._send_json(404, {'error': 'not found'})

    def do_POST(self):
        if self.path == '/melo/synthesize':
            try:
                body = self._read_body()
                text = (body.get('text') or '').strip()
                voice = body.get('voice') or 'EN-US'
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
                print(f'[melo] Error: {e}', flush=True)
                self._send_json(500, {'error': str(e)})
        else:
            self._send_json(404, {'error': 'not found'})

def main():
    init_melo()
    print(f'[melo] http://{HOST}:{PORT} — {len(VOICES)} voices, {device}', flush=True)
    server = http.server.HTTPServer((HOST, PORT), MeloHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == '__main__':
    main()
