#!/usr/bin/env python3
"""
CosyVoice TTS Provider — servidor HTTP para Personal TTS.
Usa CosyVoice-300M-Instruct de Alibaba en GPU.
Calidad cercana a Azure, funcionando 100% local.
Endpoints:
  GET  /cosyvoice/health     → { ok, voices_count, device }
  GET  /cosyvoice/voices     → { voices: [...] }
  POST /cosyvoice/synthesize → { text, voice } → WAV binario
"""

import http.server
import json
import sys
import os
import io
import time
import wave
import struct
import atexit

# Añadir torch/lib al PATH para que onnxruntime encuentre cuBLAS
_TORCH_LIB = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'Lib', 'site-packages', 'torch', 'lib')
if os.path.exists(_TORCH_LIB):
    os.environ['PATH'] = _TORCH_LIB + os.pathsep + os.environ.get('PATH', '')

# Añadir Matcha-TTS al path (necesario para CosyVoice)
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.join(_BASE, 'cosyvoice_repo')
MATCHA_DIR = os.path.join(REPO_DIR, 'third_party', 'Matcha-TTS')
if os.path.exists(MATCHA_DIR):
    sys.path.insert(0, MATCHA_DIR)
if os.path.exists(REPO_DIR):
    sys.path.insert(0, REPO_DIR)

HOST = '127.0.0.1'
PORT = 5522
MODEL_DIR = os.path.join(_BASE, 'cosyvoice_models', 'CosyVoice-300M-Instruct')
VOICE_PKG_DIR = os.path.join(_BASE, 'cosyvoice_models', 'CosyVoice-voice-pkg')

# Voces disponibles (SFT mode usa spk_id del modelo)
COSYVOICE_VOICES = [
    {'name': '中文女', 'gender': 'FEMALE', 'desc': 'CosyVoice · F · Mandarín femenina'},
    {'name': '中文男', 'gender': 'MALE', 'desc': 'CosyVoice · M · Mandarín masculina'},
    {'name': '日语男', 'gender': 'MALE', 'desc': 'CosyVoice · M · Japonés masculina'},
    {'name': '韩语女', 'gender': 'FEMALE', 'desc': 'CosyVoice · F · Coreano femenina'},
    {'name': '粤语女', 'gender': 'FEMALE', 'desc': 'CosyVoice · F · Cantonés femenina'},
    {'name': '英文女', 'gender': 'FEMALE', 'desc': 'CosyVoice · F · Inglés femenina'},
]
VOICE_NAMES = {v['name'] for v in COSYVOICE_VOICES}

# Estado global
model = None
device = 'cpu'
model_loaded = False


def download_model():
    """Descargar modelo si no existe"""
    if os.path.exists(os.path.join(MODEL_DIR, 'model.pt')) or \
       os.path.exists(os.path.join(MODEL_DIR, 'cosyvoice.yaml')):
        return True
    print(f'[cosyvoice] Descargando modelo CosyVoice-300M-Instruct...', flush=True)
    try:
        from modelscope import snapshot_download
        os.makedirs(os.path.dirname(MODEL_DIR), exist_ok=True)
        snapshot_download('iic/CosyVoice-300M-Instruct', local_dir=MODEL_DIR)
        print(f'[cosyvoice] Modelo descargado en {MODEL_DIR}', flush=True)
        return True
    except ImportError:
        try:
            from huggingface_hub import snapshot_download as hf_download
            hf_download('FunAudioLLM/CosyVoice-300M-Instruct', local_dir=MODEL_DIR)
            print(f'[cosyvoice] Modelo descargado en {MODEL_DIR}', flush=True)
            return True
        except Exception as e:
            print(f'[cosyvoice] No se pudo descargar el modelo: {e}', flush=True)
            return False
    except Exception as e:
        print(f'[cosyvoice] Error descarga: {e}', flush=True)
        return False


def init_cosyvoice():
    global model, device, model_loaded
    try:
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Descargar modelo si es necesario
        if not download_model():
            print('[cosyvoice] No se pudo obtener el modelo', flush=True)
            return False
        
        from cosyvoice.cli.cosyvoice import AutoModel
        print(f'[cosyvoice] Cargando modelo en {device}...', flush=True)
        t0 = time.time()
        model = AutoModel(model_dir=MODEL_DIR, load_jit=torch.cuda.is_available(), fp16=torch.cuda.is_available())
        model_loaded = True
        print(f'[cosyvoice] Modelo cargado en {time.time()-t0:.1f}s — GPU: {torch.cuda.memory_allocated()/1024**3:.1f}GB' if device == 'cuda' else f'[cosyvoice] Modelo cargado en {time.time()-t0:.1f}s — CPU', flush=True)
        return True
    except Exception as e:
        print(f'[cosyvoice] Error inicialización: {e}', flush=True)
        import traceback
        traceback.print_exc()
        return False


def synthesize(text, voice_name):
    global model
    if model is None:
        raise RuntimeError('CosyVoice no inicializado')
    
    # Normalizar voz
    if voice_name not in VOICE_NAMES:
        voice_name = '中文女'
    
    # Inferencia SFT (no necesita prompt de referencia)
    try:
        result_gen = model.inference_sft(text, voice_name, stream=False, text_frontend=False)
        audio_tensor = None
        for res in result_gen:
            audio_tensor = res['tts_speech']  # tensor (1, T)
            break
        
        if audio_tensor is None:
            raise RuntimeError('No se generó audio')
        
        # Convertir a numpy
        if hasattr(audio_tensor, 'cpu'):
            audio_np = audio_tensor.cpu().numpy().squeeze()
        else:
            audio_np = audio_tensor.squeeze()
        
        # Normalizar a 16-bit PCM
        max_val = max(abs(audio_np).max(), 1e-8)
        audio_int16 = (audio_np / max_val * 32767).astype('int16')
        
        sr = model.sample_rate  # 22050 Hz
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(audio_int16.tobytes())
        return buf.getvalue()
        
    except Exception as e:
        raise RuntimeError(f'CosyVoice síntesis falló: {e}')


class CosyVoiceHandler(http.server.BaseHTTPRequestHandler):
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
        if self.path == '/cosyvoice/health':
            self._send_json(200, {
                'provider': 'cosyvoice',
                'ok': model_loaded,
                'voices_count': len(COSYVOICE_VOICES),
                'device': device
            })
        elif self.path == '/cosyvoice/voices':
            voices_out = []
            for v in COSYVOICE_VOICES:
                voices_out.append({
                    'name': v['name'],
                    'gender': v['gender'],
                    'languageCode': 'zh-CN',
                    'provider': 'cosyvoice',
                    'premium': True,
                    'style': 'cosyvoice',
                    'description': v['desc']
                })
            self._send_json(200, {'voices': voices_out})
        else:
            self._send_json(404, {'error': 'not found'})

    def do_POST(self):
        if not self._check_origin(): return
        if self.path == '/cosyvoice/synthesize':
            try:
                body = self._read_body()
                text = (body.get('text') or '').strip()
                voice = body.get('voice') or '中文女'
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
                print(f'[cosyvoice] Error síntesis: {e}', flush=True)
                import traceback
                traceback.print_exc()
                self._send_json(500, {'error': str(e)})
        else:
            self._send_json(404, {'error': 'not found'})


def main():
    ok = init_cosyvoice()
    if not ok:
        print('[cosyvoice] Inicialización fallida — servidor no iniciado', flush=True)
        return
    
    server = http.server.HTTPServer((HOST, PORT), CosyVoiceHandler)
    print(f'[cosyvoice] Servidor en http://{HOST}:{PORT}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('[cosyvoice] Apagando...', flush=True)
        server.shutdown()


if __name__ == '__main__':
    main()