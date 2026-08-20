@echo off
REM ============================================================
REM  Correr el bot KitraDep en LOCAL con Gemini real.
REM  Doble-click a este archivo (o ejecutarlo en tu terminal).
REM
REM  Requisitos previos (una sola vez):
REM   1. Tener el .env con tu GEMINI_API_KEY pegada.
REM   2. El .venv ya creado con las dependencias (ya esta listo).
REM ============================================================

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No existe el entorno virtual .venv
    echo Crealo con:  uv venv .venv --python 3.12
    echo Y luego:     uv pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ERROR] No existe el archivo .env
    echo Copia .env.example a .env y pega tu GEMINI_API_KEY
    pause
    exit /b 1
)

echo ============================================================
echo  Arrancando KitraDep... (Ctrl+C para detener)
echo  Se abrira el navegador en http://127.0.0.1:8765
echo ============================================================
".venv\Scripts\python.exe" webapp_hibrida.py

pause
