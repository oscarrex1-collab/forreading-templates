#!/usr/bin/env python3
"""
Kokoro TTS Provider — servidor HTTP para Personal TTS.
Carga Kokoro en GPU una vez, sirve síntesis local sin API keys.
Endpoints:
  GET  /kokoro/health     → { ok, voices_count, device }
  GET  /kokoro/voices     → { voices: [{ name, gender, ... }] }
  POST /kokoro/synthesize → { text, voice } → WAV binario
"""

import http.server
import json
import os
import sys
import io
import time
import wave
import struct

# ── Config ──
HOST = '127.0.0.1'
PORT = 5520

# 20 mejores voces Kokoro para mandarín
VOICES = [
    # Femeninas (10)
    {'name': 'zf_001', 'gender': 'FEMALE', 'desc': 'Kokoro · F · Principal'},
    {'name': 'zf_003', 'gender': 'FEMALE', 'desc': 'Kokoro · F · Natural'},
    {'name': 'zf_004', 'gender': 'FEMALE', 'desc': 'Kokoro · F · Cálida'},
    {'name': 'zf_008', 'gender': 'FEMALE', 'desc': 'Kokoro · F · Clara'},
    {'name': 'zf_018', 'gender': 'FEMALE', 'desc': 'Kokoro · F · Suave'},
    {'name': 'zf_021', 'gender': 'FEMALE', 'desc': 'Kokoro · F · Expresiva'},
    {'name': 'zf_024', 'gender': 'FEMALE', 'desc': 'Kokoro · F · Narrativa'},
    {'name': 'zf_032', 'gender': 'FEMALE', 'desc': 'Kokoro · F · Juvenil'},
    {'name': 'zf_039', 'gender': 'FEMALE', 'desc': 'Kokoro · F · Serena'},
    {'name': 'zf_051', 'gender': 'FEMALE', 'desc': 'Kokoro · F · Profesional'},
    # Masculinas (10)
    {'name': 'zm_009', 'gender': 'MALE', 'desc': 'Kokoro · M · Principal'},
    {'name': 'zm_010', 'gender': 'MALE', 'desc': 'Kokoro · M · Profunda'},
    {'name': 'zm_016', 'gender': 'MALE', 'desc': 'Kokoro · M · Neutra'},
    {'name': 'zm_020', 'gender': 'MALE', 'desc': 'Kokoro · M · Narrativa'},
    {'name': 'zm_025', 'gender': 'MALE', 'desc': 'Kokoro · M · Cálida'},
    {'name': 'zm_030', 'gender': 'MALE', 'desc': 'Kokoro · M · Conversacional'},
    {'name': 'zm_041', 'gender': 'MALE', 'desc': 'Kokoro · M · Seria'},
    {'name': 'zm_050', 'gender': 'MALE', 'desc': 'Kokoro · M · Enérgica'},
    {'name': 'zm_069', 'gender': 'MALE', 'desc': 'Kokoro · M · Suave'},
    {'name': 'zm_082', 'gender': 'MALE', 'desc': 'Kokoro · M · Versátil'},
]
VOICE_NAMES = {v['name'] for v in VOICES}

# ── Estado global ──
model = None
pipeline = None
device = 'cpu'
loaded_voices = {}
ready = False


def init_kokoro():
    global model, pipeline, device, ready
    try:
        from kokoro import KPipeline, KModel
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f'[kokoro] Cargando modelo en {device}...', flush=True)
        t0 = time.time()
        model = KModel(repo_id='hexgrad/Kokoro-82M-v1.1-zh').to(device).eval()
        pipeline = KPipeline(lang_code='z', repo_id='hexgrad/Kokoro-82M-v1.1-zh', model=model)
        print(f'[kokoro] Modelo cargado en {time.time()-t0:.1f}s', flush=True)
        # Precargar la primera voz (zf_001)
        load_voice('zf_001')
        print(f'[kokoro] Voz zf_001 precargada', flush=True)
        if device == 'cuda':
            # Warm-up: primera inferencia (CUDA compilation)
            gen = pipeline('今天天气真不错。', voice='zf_001')
            next(gen)
            print(f'[kokoro] Warm-up completo', flush=True)
        ready = True
        print(f'[kokoro] Listo en {time.time()-t0:.1f}s — {len(VOICES)} voces, GPU: {torch.cuda.memory_allocated()/1024**3:.1f}GB' if device == 'cuda' else f'[kokoro] Listo en {time.time()-t0:.1f}s — {len(VOICES)} voces, CPU', flush=True)
    except Exception as e:
        print(f'[kokoro] Error de inicialización: {e}', flush=True)
        ready = False


def load_voice(name):
    if name in loaded_voices:
        return loaded_voices[name]
    if pipeline is None:
        raise RuntimeError('Kokoro no inicializado')
    voice = pipeline.load_voice(name)
    loaded_voices[name] = voice
    return voice


def synthesize(text, voice_name):
    if not ready or pipeline is None:
        raise RuntimeError('Kokoro no disponible')
    if voice_name not in VOICE_NAMES:
        voice_name = 'zf_001'
    load_voice(voice_name)
    gen = pipeline(text, voice=voice_name)
    result = next(gen)
    audio = result.audio.cpu().numpy()
    # Normalizar a 16-bit PCM
    max_val = max(abs(audio).max(), 1e-8)
    audio_int16 = (audio / max_val * 32767 * 0.95).astype('int16')
    sr = 24000
    # Escribir WAV en buffer
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()


# ── HTTP Server ──
class KokoroHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Silencioso

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
        if length == 0:
            return {}
        data = self.rfile.read(length)
        return json.loads(data.decode('utf-8'))

    def _check_origin(self):
        # 🔒 Solo aceptar requests sin Origin (scripts locales, curl) o desde extensiones Chrome
        origin = self.headers.get('Origin', '')
        if not origin:
            return True
        if origin.startswith('chrome-extension://') or origin.startswith('moz-extension://'):
            return True
        self._send_json(403, {'error': 'origin not allowed'})
        return False

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if not self._check_origin(): return
        if self.path == '/kokoro/health':
            self._send_json(200, {
                'provider': 'kokoro',
                'ok': ready,
                'voices_count': len(VOICES),
                'device': device
            })
        elif self.path == '/kokoro/voices':
            voices_out = []
            for v in VOICES:
                voices_out.append({
                    'name': v['name'],
                    'gender': v['gender'],
                    'languageCode': 'zh-CN',
                    'provider': 'kokoro',
                    'premium': False,
                    'style': 'kokoro',
                    'description': v['desc']
                })
            self._send_json(200, {'voices': voices_out})
        else:
            self._send_json(404, {'error': 'not found'})

    def do_POST(self):
        if not self._check_origin(): return
        if self.path == '/kokoro/synthesize':
            try:
                body = self._read_body()
                text = (body.get('text') or '').strip()
                voice = body.get('voice') or 'zf_001'
                if not text:
                    self._send_json(400, {'error': 'texto vacío'})
                    return
                wav_data = synthesize(text, voice)
                self.send_response(200)
                self.send_header('Content-Type', 'audio/wav')
                self.send_header('Content-Length', str(len(wav_data)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(wav_data)
            except Exception as e:
                print(f'[kokoro] Error síntesis: {e}', flush=True)
                self._send_json(500, {'error': str(e)})
        else:
            self._send_json(404, {'error': 'not found'})


def main():
    # Inicializar Kokoro (puede tardar unos segundos)
    init_kokoro()
    server = http.server.HTTPServer((HOST, PORT), KokoroHandler)
    print(f'[kokoro] Servidor en http://{HOST}:{PORT}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('[kokoro] Apagando...', flush=True)
        server.shutdown()


if __name__ == '__main__':
    main()