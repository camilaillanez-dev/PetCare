@echo off
setlocal
cd /d "%~dp0"

rem Reuse an already-running local instance when possible.
powershell -NoProfile -Command "try { Invoke-RestMethod 'http://127.0.0.1:8765/api/health' -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }"
if not errorlevel 1 goto open_app

rem Prefer the Python runtime bundled with Codex; fall back to Python Launcher.
set "PETCARE_PY=C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1123-915-0_26.1123.915.0_x64__3k8sg7r9htsxt\dependencies\python\python.exe"
if not exist "%PETCARE_PY%" set "PETCARE_PY="
if not defined PETCARE_PY (
  where py >nul 2>nul
  if not errorlevel 1 set "PETCARE_PY=py -3"
)
if not defined PETCARE_PY (
  echo No se encontro Python 3.10 o posterior.
  echo Instala Python o inicia PetCare desde Codex.
  pause
  exit /b 1
)

if "%PETCARE_PY%"=="py -3" (
  start "PetCare - servidor local" /min py -3 server.py
) else (
  start "PetCare - servidor local" /min "%PETCARE_PY%" server.py
)
timeout /t 2 /nobreak >nul

:open_app
start "" "http://127.0.0.1:8765/clinic.html"
endlocal
