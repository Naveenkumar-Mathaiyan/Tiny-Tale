@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Missing Python environment. Complete the README setup first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" run_local.py admin
pause
