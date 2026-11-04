@echo off
REM Double-click to test the public API. Add "trigger" to also cut a new clip:
REM   test_api.bat trigger
if /i "%~1"=="trigger" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0test_api.ps1" -Trigger
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0test_api.ps1"
)
pause
