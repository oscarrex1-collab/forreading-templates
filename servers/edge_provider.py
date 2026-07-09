#!/usr/bin/env python3
"""
Edge-TTS Provider — servidor HTTP para Personal TTS.
Usa la API gratuita de Microsoft Edge TTS (sin API key).
Voces obtenidas dinámicamente de Microsoft.
Endpoints:
  GET  /edge/health     → { ok, voices_count }
  GET  /edge/voices     → { voices: [{ name, gender, locale, ... }] }
  POST /edge/synthesize → { text, voice } → { audio: base64, boundaries: [...] }
"""

import http.server
import json
import asyncio
import base64
import edge_tts
from edge_tts import Communicate

HOST = '127.0.0.1'
PORT = 5521

ready = False
loop = None
voice_cache = []          # lista de voces válidas
voice_names = set()       # { name } para validación rápida
last_voice_refresh = 0


async def refresh_voices():
    """Obtener voces disponibles del servidor de Microsoft y cachear."""
    global voice_cache, voice_names, last_voice_refresh
    try:
        all_voices = await edge_tts.list_voices()
        if not all_voices:
            return voice_cache
        voice_cache = []
        for v in all_voices:
            short_name = v.get('ShortName', '')
            if not short_name:
                continue
            gender = v.get('Gender', 'Female')
            locale = v.get('Locale', 'zh-CN')
            is_hd = 'DragonHD' in short_name
            is_premium = v.get('VoiceType', '') == 'Premium' or is_hd
            voice_cache.append({
                'name': short_name,
                'gender': 'MALE' if gender == 'Male' else 'FEMALE',
                'languageCode': locale,
                'provider': 'edge',
                'premium': is_premium,
                'style': 'dragonhd' if is_hd else 'neural',
                'description': f'Edge · {"M" if gender == "Male" else "F"} · {locale} · {short_name.replace(locale + "-", "")}'
            })
        voice_names = {v['name'] for v in voice_cache}
        import time
        last_voice_refresh = time.time()
        print(f'[edge] {len(voice_cache)} voces chinas cargadas dinámicamente', flush=True)
    except Exception as e:
        print(f'[edge] Error refreshing voices: {e}', flush=True)
    return voice_cache


def rate_to_edge_str(rate_num):
    """Convierte rate numérico (0.5-2.5) a formato edge-tts (+/-%)."""
    pct = int(round((rate_num - 1.0) * 100))
    return f"{pct:+d}%"


async def synthesize_with_boundaries(text, voice_name, rate_str="+0%"):
    """
    Generar audio y word boundaries en una SOLA llamada a edge-tts.
    Devuelve (audio_bytes, boundaries_list).
    """
    com = Communicate(text, voice_name, rate=rate_str, boundary='WordBoundary')
    chunks = []
    boundaries = []
    async for chunk in com.stream():
        if chunk['type'] == 'audio':
            chunks.append(chunk['data'])
        elif chunk['type'] == 'WordBoundary':
            boundaries.append({
                'text': chunk['text'],
                'offset': chunk['offset'],
                'duration': chunk['duration'],
                'type': 'Word'
            })
    if not chunks:
        raise RuntimeError('No audio was received. Please verify that your parameters are correct.')
    audio_data = b''.join(chunks)
    return audio_data, boundaries


async def synthesize_audio_only(text, voice_name, rate_str="+0%"):
    """Fallback: generar solo audio sin boundaries."""
    com = Communicate(text, voice_name, rate=rate_str)
    chunks = []
    async for chunk in com.stream():
        if chunk['type'] == 'audio':
            chunks.append(chunk['data'])
    if not chunks:
        raise RuntimeError('No audio was received. Please verify that your parameters are correct.')
    return b''.join(chunks), []


class EdgeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

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
        return json.loads(self.rfile.read(length).decode('utf-8'))

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
        if self.path == '/edge/health':
            self._send_json(200, {'provider': 'edge', 'ok': ready, 'voices_count': len(voice_cache)})
        elif self.path == '/edge/voices':
            # Refrescar si está vacío
            if not voice_cache:
                global loop
                if loop is None or loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.run_until_complete(refresh_voices())
            self._send_json(200, {'voices': voice_cache})
        else:
            self._send_json(404, {'error': 'not found'})

    def do_POST(self):
        global loop
        if not self._check_origin(): return
        if self.path == '/edge/synthesize':
            try:
                body = self._read_body()
                text = (body.get('text') or '').strip()
                voice = body.get('voice') or ''
                rate_num = float(body.get('rate', 1.0))
                rate_str = rate_to_edge_str(rate_num)
                if not text:
                    self._send_json(400, {'error': 'texto vacío'})
                    return
                # Si la voz no está en la lista conocida, confiar en el nombre o usar default
                if voice not in voice_names:
                    # Usar la primera voz china disponible como fallback
                    if voice_names:
                        voice = next(iter(voice_names))
                    else:
                        voice = 'zh-CN-XiaoxiaoNeural'

                if loop is None or loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Intentar con WordBoundary; fallback a solo audio
                try:
                    mp3_data, boundaries = loop.run_until_complete(
                        synthesize_with_boundaries(text, voice, rate_str)
                    )
                except Exception as e:
                    error_msg = str(e)
                    print(f'[edge] WordBoundary falló para "{voice}", reintentando sin boundaries: {error_msg[:80]}', flush=True)
                    mp3_data, boundaries = loop.run_until_complete(
                        synthesize_audio_only(text, voice, rate_str)
                    )

                audio_b64 = base64.b64encode(mp3_data).decode('ascii')
                self._send_json(200, {
                    'audio': audio_b64,
                    'boundaries': boundaries
                })
            except Exception as e:
                print(f'[edge] Error síntesis: {e}', flush=True)
                self._send_json(500, {'error': str(e)})
        elif self.path == '/edge/boundaries':
            self._send_json(410, {'error': 'obsoleto: usa /edge/synthesize'})
        else:
            self._send_json(404, {'error': 'not found'})


def main():
    global loop, ready
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Refrescar voces al arrancar
    try:
        loop.run_until_complete(refresh_voices())
    except Exception as e:
        print(f'[edge] No se pudieron cargar voces al inicio: {e}', flush=True)
        # Fallback mínimo
        global voice_cache, voice_names
        voice_cache = [{'name': 'zh-CN-XiaoxiaoNeural', 'gender': 'FEMALE', 'languageCode': 'zh-CN', 'provider': 'edge', 'premium': True, 'style': 'neural', 'description': 'Edge · F · zh-CN · XiaoxiaoNeural (fallback)'}]
        voice_names = {'zh-CN-XiaoxiaoNeural'}
    ready = True
    server = http.server.HTTPServer((HOST, PORT), EdgeHandler)
    print(f'[edge] Servidor en http://{HOST}:{PORT}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('[edge] Apagando...', flush=True)
        server.shutdown()


if __name__ == '__main__':
    main()