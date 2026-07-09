@echo off
REM ForReading Community TTS Server Launcher
REM Starts local TTS sidecars. Each runs on its own port.
REM
REM Quick start (no GPU, no API key):
REM   pip install edge-tts piper-tts
REM   launcher.bat
REM
REM All providers expose 3 endpoints:
REM   GET  /<name>/health     -> {"ok": true, "voices_count": N}
REM   GET  /<name>/voices     -> {"voices": [...]}
REM   POST /<name>/synthesize -> audio binary

title ForReading TTS Servers
echo ========================================
echo   ForReading - Local TTS Servers
echo ========================================
echo.

set SCRIPT_DIR=%~dp0

REM ==== No GPU needed ====

echo [1] Edge TTS :5521 (300+ voices, 100+ languages)
start "Edge :5521" /MIN python "%SCRIPT_DIR%edge_provider.py"

echo [2] Piper :5525 (100+ voices, CPU, ultra-fast)
start "Piper :5525" /MIN python "%SCRIPT_DIR%piper_provider.py"

echo [3] MeloTTS :5526 (6 languages, CPU-friendly)
start "Melo :5526" /MIN python "%SCRIPT_DIR%melo_provider.py"

REM ==== GPU recommended ====
REM Uncomment the ones you want:

REM echo [4] Kokoro :5520 (44 voices EN+ZH+JA)
REM start "Kokoro :5520" /MIN python "%SCRIPT_DIR%kokoro_provider.py"

REM echo [5] XTTS :5527 (17 languages, voice cloning)
REM start "XTTS :5527" /MIN python "%SCRIPT_DIR%xtts_provider.py"

REM echo [6] CosyVoice :5522 (Chinese premium)
REM start "CosyVoice :5522" /MIN python "%SCRIPT_DIR%cosyvoice_provider.py"

echo.
echo ========================================
echo   All providers and ports:
echo     Edge     :5521  (free, no GPU, no setup)
echo     Piper    :5525  (100+ voices, CPU)
echo     MeloTTS  :5526  (6 languages, CPU)
echo     Kokoro   :5520  (GPU, 44 voices EN+ZH+JA)
echo     XTTS     :5527  (GPU, 17 languages, cloning)
echo     CosyVoice:5522  (GPU, Chinese premium)
echo.
echo   To add your own: copy _TEMPLATE_provider.py
echo   and edit the voice list + synthesize()
echo ========================================
echo.
pause
