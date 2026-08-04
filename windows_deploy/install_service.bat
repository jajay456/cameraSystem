@echo off
REM Registers the KROSS Replay server as a Windows Service named "KrossReplay"
REM using NSSM, so it starts automatically at boot (even before anyone logs
REM in) and restarts itself if it crashes.
REM
REM NOT YET TESTED ON WINDOWS — written from macOS. Run this, and if
REM anything errors, report the exact message back so it can be fixed.
REM
REM --- One-time setup before running this file ---
REM 1. Download NSSM from https://nssm.cc/download, unzip it, and note the
REM    path to nssm.exe (use the win64 folder on a 64-bit machine).
REM 2. Edit NSSM_EXE and PROJECT_DIR below to match this machine.
REM 3. Make sure `pip install -r requirements.txt` has already been run
REM    inside PROJECT_DIR\.venv on this machine.
REM 4. Right-click this file -> "Run as administrator".

set NSSM_EXE=C:\nssm\nssm.exe
set PROJECT_DIR=C:\KrossReplay\camera_system
set PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe
set SERVICE_NAME=KrossReplay

if not exist "%NSSM_EXE%" (
    echo ERROR: nssm.exe not found at %NSSM_EXE%
    echo Download it from https://nssm.cc/download and edit NSSM_EXE above.
    exit /b 1
)
if not exist "%PYTHON_EXE%" (
    echo ERROR: python.exe not found at %PYTHON_EXE%
    echo Create the venv first: cd %PROJECT_DIR% ^&^& python -m venv .venv
    echo Then: %PROJECT_DIR%\.venv\Scripts\pip install -r requirements.txt
    exit /b 1
)

if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

"%NSSM_EXE%" install %SERVICE_NAME% "%PYTHON_EXE%" "-m app.main"
"%NSSM_EXE%" set %SERVICE_NAME% AppDirectory "%PROJECT_DIR%"
"%NSSM_EXE%" set %SERVICE_NAME% AppStdout "%PROJECT_DIR%\logs\server.log"
"%NSSM_EXE%" set %SERVICE_NAME% AppStderr "%PROJECT_DIR%\logs\server.log"
"%NSSM_EXE%" set %SERVICE_NAME% AppRotateFiles 1
"%NSSM_EXE%" set %SERVICE_NAME% AppRotateBytes 10485760
"%NSSM_EXE%" set %SERVICE_NAME% Start SERVICE_AUTO_START
"%NSSM_EXE%" start %SERVICE_NAME%

echo.
echo Done. The service "%SERVICE_NAME%" is installed and should be starting.
echo Check status with:  sc query %SERVICE_NAME%
echo View logs at:        %PROJECT_DIR%\logs\server.log
echo Open the dashboard:  http://localhost:8000
