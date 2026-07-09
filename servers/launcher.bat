@echo off
REM ForReading — Community TTS Server Launcher
REM Starts all local TTS sidecars. Edit this file to add/remove providers.
REM Each provider runs on its own port and exposes 3 endpoints:
REM   GET  /<name>/health     → {"ok": true, "voices_count": N}
REM   GET  /<name>/voices     → {"voices": [...]}
REM   POST /<name>/synthesize → audio binary
title ForReading TTS Servers
echo ========================================
echo   ForReading — Local TTS Servers
echo ========================================
echo.

set SCRIPT_DIR=%~dp0

REM ---- Edge TTS (:5521) - Free, no GPU, no API key ----
echo [1/3] Starting Edge TTS :5521...
start "Edge TTS :5521" /MIN python "%SCRIPT_DIR%edge_provider.py"

REM ---- Kokoro (:5520) - GPU recommended, 20 neural voices ----
REM Uncomment and adjust python path if you have Kokoro installed:
REM echo [2/3] Starting Kokoro :5520...
REM start "Kokoro :5520" /MIN python "%SCRIPT_DIR%kokoro_provider.py"

REM ---- CosyVoice (:5522) - GPU recommended, Chinese voices ----
REM Uncomment if you have CosyVoice installed:
REM echo [3/3] Starting CosyVoice :5522...
REM start "CosyVoice :5522" /MIN python "%SCRIPT_DIR%cosyvoice_provider.py"

echo.
echo ========================================
echo   Servers started:
echo     Edge TTS   :5521  (free, no setup)
echo     Kokoro     :5520  (uncomment to enable)
echo     CosyVoice  :5522  (uncomment to enable)
echo.
echo   To stop: close the console windows or run:
echo     taskkill /F /IM python.exe
echo ========================================
echo.
pause
