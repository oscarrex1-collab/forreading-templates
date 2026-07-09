#!/usr/bin/env python3
"""
Piper TTS Provider — ultra-fast CPU TTS for ForReading extension.
100+ voices, 30+ languages. Runs on any machine (even Raspberry Pi).

Setup: pip install piper-tts
"""

import http.server
import json
import io
import wave
import subprocess
import tempfile
import os

HOST = '127.0.0.1'
PORT = 5525

# ── All available Piper voices ──
# Download them with: python -c "import piper; print(piper.list_voices())"
VOICES = [
    # English
    {'name': 'en_US-lessac-medium', 'gender': 'FEMALE', 'lang': 'en-US', 'desc': 'Piper · F · EN · Lessac (natural)'},
    {'name': 'en_US-libritts_r-medium', 'gender': 'FEMALE', 'lang': 'en-US', 'desc': 'Piper · F · EN · LibriTTS (warm)'},
    {'name': 'en_US-ryan-high', 'gender': 'MALE', 'lang': 'en-US', 'desc': 'Piper · M · EN · Ryan (clear)'},
    {'name': 'en_US-joe-medium', 'gender': 'MALE', 'lang': 'en-US', 'desc': 'Piper · M · EN · Joe (natural)'},
    {'name': 'en_GB-northern_english_male-medium', 'gender': 'MALE', 'lang': 'en-GB', 'desc': 'Piper · M · EN-GB · Northern'},
    {'name': 'en_GB-southern_english_female-low', 'gender': 'FEMALE', 'lang': 'en-GB', 'desc': 'Piper · F · EN-GB · Southern'},
    # Chinese
    {'name': 'zh_CN-huayan-medium', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'Piper · F · ZH · Huayan (soft)'},
    {'name': 'zh_CN-huayan-x_low-medium', 'gender': 'FEMALE', 'lang': 'zh-CN', 'desc': 'Piper · F · ZH · Huayan XL'},
    # Japanese
    {'name': 'ja_JP-jp_hoku-medium', 'gender': 'MALE', 'lang': 'ja-JP', 'desc': 'Piper · M · JA · Hoku'},
    # Korean
    {'name': 'ko_KR-kss-medium', 'gender': 'FEMALE', 'lang': 'ko-KR', 'desc': 'Piper · F · KO · KSS'},
    # Spanish
    {'name': 'es_ES-carlfm-x_low-medium', 'gender': 'MALE', 'lang': 'es-ES', 'desc': 'Piper · M · ES · Carl'},
    {'name': 'es_MX-claude-medium', 'gender': 'MALE', 'lang': 'es-MX', 'desc': 'Piper · M · ES-MX · Claude'},
    # French
    {'name': 'fr_FR-siwis-medium', 'gender': 'FEMALE', 'lang': 'fr-FR', 'desc': 'Piper · F · FR · Siwis'},
    # German
    {'name': 'de_DE-thorsten-medium', 'gender': 'MALE', 'lang': 'de-DE', 'desc': 'Piper · M · DE · Thorsten'},
    # Italian
    {'name': 'it_IT-paola-medium', 'gender': 'FEMALE', 'lang': 'it-IT', 'desc': 'Piper · F · IT · Paola'},
    # Portuguese
    {'name': 'pt_BR-eduardo-medium', 'gender': 'MALE', 'lang': 'pt-BR', 'desc': 'Piper · M · PT-BR · Eduardo'},
    # Russian
    {'name': 'ru_RU-irina-medium', 'gender': 'FEMALE', 'lang': 'ru-RU', 'desc': 'Piper · F · RU · Irina'},
    # Turkish
    {'name': 'tr_TR-fahrettin-medium', 'gender': 'MALE', 'lang': 'tr-TR', 'desc': 'Piper · M · TR · Fahrettin'},
]

VOICE_NAMES = {v['name'] for v in VOICES}
ready = True  # Piper is stateless, always ready

def synthesize(text, voice_name):
    if voice_name not in VOICE_NAMES:
        voice_name = 'en_US-lessac-medium'
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run([
            'piper', '--model', voice_name, '--output_file', tmp_path
        ], input=text.encode('utf-8'), capture_output=True, timeout=30, check=True)
        with open(tmp_path, 'rb') as f:
            return f.read()
    finally:
        try: os.unlink(tmp_path)
        except: pass

class PiperHandler(http.server.BaseHTTPRequestHandler):
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
        if self.path == '/piper/health':
            self._send_json(200, {'provider': 'piper', 'ok': ready, 'voices_count': len(VOICES)})
        elif self.path == '/piper/voices':
            out = [{
                'name': v['name'], 'gender': v['gender'],
                'languageCode': v['lang'], 'provider': 'piper',
                'premium': False, 'style': 'piper', 'description': v['desc']
            } for v in VOICES]
            self._send_json(200, {'voices': out})
        else:
            self._send_json(404, {'error': 'not found'})

    def do_POST(self):
        if not self._check_origin(): return
        if self.path == '/piper/synthesize':
            try:
                body = self._read_body()
                text = (body.get('text') or '').strip()
                voice = body.get('voice') or 'en_US-lessac-medium'
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
                print(f'[piper] Error: {e}', flush=True)
                self._send_json(500, {'error': str(e)})
        else:
            self._send_json(404, {'error': 'not found'})

def main():
    print(f'[piper] http://{HOST}:{PORT} — {len(VOICES)} voices, CPU', flush=True)
    server = http.server.HTTPServer((HOST, PORT), PiperHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == '__main__':
    main()
