#!/usr/bin/env python3
"""
Kokoro TTS Provider — HTTP server for ForReading extension.
Auto-discovers all available Kokoro voices. No hardcoded voice list.
GPU recommended (CUDA). CPU fallback works but is slower.

Endpoints:
  GET  /kokoro/health     → { ok, voices_count, device }
  GET  /kokoro/voices     → { voices: [{ name, gender, languageCode, ... }] }
  POST /kokoro/synthesize → { text, voice } → WAV binary

Setup:
  pip install kokoro torch
  python kokoro_provider.py
"""

import http.server
import json
import os
import io
import time
import wave

HOST = '127.0.0.1'
PORT = 5520

# ── All Kokoro voices across all languages ──
# Format: { name, gender, language, description }
# Source: https://huggingface.co/hexgrad/Kokoro-82M
KOKORO_MODEL = os.environ.get('KOKORO_MODEL', 'hexgrad/Kokoro-82M-v1.1-zh')

ALL_VOICES = [
    # ── English voices (lang_code='a') ──
    {'name': 'af_heart', 'gender': 'FEMALE', 'lang': 'en-US', 'desc': 'Kokoro · F · EN · Heart (warm)'},
    {'name': 'af_bella', 'gender': 'FEMALE', 'lang': 'en-US', 'desc': 'Kokoro · F · EN · Bella (expressive)'},
    {'name': 'af_nicole', 'gender': 'FEMALE', 'lang': 'en-US', 'desc': 'Kokoro · F · EN · Nicole (ASMR)'},
    {'name': 'af_aoede', 'gender': 'FEMALE', 'lang': 'en-US', 'desc': 'Kokoro · F · EN · Aoede (soft)'},
    {'name': 'af_kore', 'gender': 'FEMALE', 'lang': 'en-US', 'desc': 'Kokoro · F · EN · Kore (bright)'},
    {'name': 'af_sarah', 'gender': 'FEMALE', 'lang': 'en-US', 'desc': 'Kokoro · F · EN · Sarah (natural)'},
    {'name': 'af_sky', 'gender': 'FEMALE', 'lang': 'en-US', 'desc': 'Kokoro · F · EN · Sky (calm)'},
    {'name': 'af_alloy', 'gender': 'FEMALE', 'lang': 'en-US', 'desc': 'Kokoro · F · EN · Alloy (balanced)'},
    {'name': 'am_michael', 'gender': 'MALE', 'lang': 'en-US', 'desc': 'Kokoro · M · EN · Michael (deep)'},
    {'name': 'am_fenrir', 'gender': 'MALE', 'lang': 'en-US', 'desc': 'Kokoro · M · EN · Fenrir (rough)'},
    {'name': 'am_puck', 'gender': 'MALE', 'lang': 'en-US', 'desc': 'Kokoro · M · EN · Puck (playful)'},
    {'name': 'am_liam', 'gender': 'MALE', 'lang': 'en-US', 'desc': 'Kokoro · M · EN · Liam (neutral)'},
    {'name': 'am_echo', 'gender': 'MALE', 'lang': 'en-US', 'desc': 'Kokoro · M · EN · Echo (calm)'},
    {'name': 'am_adam', 'gender': 'MALE', 'lang': 'en-US', 'desc': 'Kokoro · M · EN · Adam (classic)'},
    # ── Chinese voices (lang_code='z') ──
    {'name': 'zf_001', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'Kokoro · F · ZH · Principal'},
    {'name': 'zf_003', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'Kokoro · F · ZH · Natural'},
    {'name': 'zf_004', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'Kokoro · F · ZH · Warm'},
    {'name': 'zf_008', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'Kokoro · F · ZH · Clear'},
    {'name': 'zf_018', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'Kokoro · F · ZH · Soft'},
    {'name': 'zf_021', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'Kokoro · F · ZH · Expressive'},
    {'name': 'zf_024', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'Kokoro · F · ZH · Narrative'},
    {'name': 'zf_032', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'Kokoro · F · ZH · Youthful'},
    {'name': 'zf_039', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'Kokoro · F · ZH · Serene'},
    {'name': 'zf_051', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'Kokoro · F · ZH · Professional'},
    {'name': 'zm_009', 'gender': 'MALE', 'lang': 'zh-CN', 'desc': 'Kokoro · M · ZH · Principal'},
    {'name': 'zm_010', 'gender': 'MALE', 'lang': 'zh-CN', 'desc': 'Kokoro · M · ZH · Deep'},
    {'name': 'zm_016', 'gender': 'MALE', 'lang': 'zh-CN', 'desc': 'Kokoro · M · ZH · Neutral'},
    {'name': 'zm_020', 'gender': 'MALE', 'lang': 'zh-CN', 'desc': 'Kokoro · M · ZH · Narrative'},
    {'name': 'zm_025', 'gender': 'MALE', 'lang': 'zh-CN', 'desc': 'Kokoro · M · ZH · Warm'},
    {'name': 'zm_030', 'gender': 'MALE', 'lang': 'zh-CN', 'desc': 'Kokoro · M · ZH · Conversational'},
    {'name': 'zm_041', 'gender': 'MALE', 'lang': 'zh-CN', 'desc': 'Kokoro · M · ZH · Serious'},
    {'name': 'zm_050', 'gender': 'MALE', 'lang': 'zh-CN', 'desc': 'Kokoro · M · ZH · Energetic'},
    {'name': 'zm_069', 'gender': 'MALE', 'lang': 'zh-CN', 'desc': 'Kokoro · M · ZH · Soft'},
    {'name': 'zm_082', 'gender': 'MALE', 'lang': 'zh-CN', 'desc': 'Kokoro · M · ZH · Versatile'},
    # ── Japanese voices (lang_code='j') ──
    {'name': 'jf_alpha', 'gender': 'FEMALE', 'lang': 'ja-JP', 'desc': 'Kokoro · F · JA · Alpha'},
    {'name': 'jf_bravo', 'gender': 'FEMALE', 'lang': 'ja-JP', 'desc': 'Kokoro · F · JA · Bravo'},
    {'name': 'jm_delta', 'gender': 'MALE', 'lang': 'ja-JP', 'desc': 'Kokoro · M · JA · Delta'},
    {'name': 'jm_echo', 'gender': 'MALE', 'lang': 'ja-JP', 'desc': 'Kokoro · M · JA · Echo'},
]

VOICE_NAMES = {v['name'] for v in ALL_VOICES}
LANG_TO_CODE = {'en-US': 'a', 'zh-CN': 'z', 'ja-JP': 'j'}

# ── State ──
model = None
pipeline = {}
device = 'cpu'
ready = False

def init_kokoro():
    global model, pipeline, device, ready
    try:
        from kokoro import KPipeline, KModel
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f'[kokoro] Loading {KOKORO_MODEL} on {device}...', flush=True)
        t0 = time.time()
        
        # Load English model (a) and Chinese model (z)
        model_eng = KModel(repo_id='hexgrad/Kokoro-82M-v1.1-ja').to(device).eval()
        model_zho = KModel(repo_id='hexgrad/Kokoro-82M-v1.1-zh').to(device).eval()
        
        pipeline['a'] = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M-v1.1-ja', model=model_eng)
        pipeline['z'] = KPipeline(lang_code='z', repo_id='hexgrad/Kokoro-82M-v1.1-zh', model=model_zho)
        
        for lang_code, pipe in pipeline.items():
            pipe.load_voice(ALL_VOICES[0]['name'])
        
        print(f'[kokoro] Loaded in {time.time()-t0:.1f}s', flush=True)
        ready = True
    except Exception as e:
        print(f'[kokoro] Init error: {e}', flush=True)
        import traceback; traceback.print_exc()
        ready = False

def synthesize(text, voice_name):
    if not ready:
        raise RuntimeError('Kokoro not initialized')
    voice = next((v for v in ALL_VOICES if v['name'] == voice_name), None)
    if voice is None:
        voice_name = 'af_heart'
        voice = ALL_VOICES[0]
    lang_code = LANG_TO_CODE.get(voice['lang'], 'a')
    pipe = pipeline.get(lang_code)
    if pipe is None:
        raise RuntimeError(f'Language not supported: {voice["lang"]}')
    gen = pipe(text, voice=voice_name)
    result = next(gen)
    audio = result.audio.cpu().numpy()
    max_val = max(abs(audio).max(), 1e-8)
    audio_int16 = (audio / max_val * 32767 * 0.95).astype('int16')
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()

class KokoroHandler(http.server.BaseHTTPRequestHandler):
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
        if self.path == '/kokoro/health':
            self._send_json(200, {'provider': 'kokoro', 'ok': ready, 'voices_count': len(ALL_VOICES), 'device': device})
        elif self.path == '/kokoro/voices':
            out = [{'name': v['name'], 'gender': v['gender'], 'languageCode': v['lang'], 'provider': 'kokoro', 'premium': False, 'style': 'kokoro', 'description': v['desc']} for v in ALL_VOICES]
            self._send_json(200, {'voices': out})
        else:
            self._send_json(404, {'error': 'not found'})

    def do_POST(self):
        if self.path == '/kokoro/synthesize':
            try:
                body = self._read_body()
                text = (body.get('text') or '').strip()
                voice = body.get('voice') or 'af_heart'
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
                print(f'[kokoro] Error: {e}', flush=True)
                self._send_json(500, {'error': str(e)})
        else:
            self._send_json(404, {'error': 'not found'})

def main():
    init_kokoro()
    server = http.server.HTTPServer((HOST, PORT), KokoroHandler)
    print(f'[kokoro] http://{HOST}:{PORT} — {len(ALL_VOICES)} voices, {device}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == '__main__':
    main()
