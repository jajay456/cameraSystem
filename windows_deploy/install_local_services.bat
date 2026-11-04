@echo off
setlocal
REM Run as Administrator after editing NSSM_EXE and PROJECT_DIR.

set NSSM_EXE=C:\nssm\nssm.exe
set PROJECT_DIR=C:\KrossReplay\camera_system
set PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe
set NODE_EXE=C:\Program Files\nodejs\node.exe
set NPM_CMD=C:\Program Files\nodejs\npm.cmd
set CLOUDFLARED_EXE=C:\Program Files\cloudflared\cloudflared.exe

if not exist "%NSSM_EXE%" echo ERROR: NSSM not found & exit /b 1
if not exist "%PYTHON_EXE%" echo ERROR: Python venv not found & exit /b 1
if not exist "%NPM_CMD%" echo ERROR: npm not found & exit /b 1
if not exist "%CLOUDFLARED_EXE%" echo ERROR: cloudflared not found & exit /b 1
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

call :install KrossReplay "%PYTHON_EXE%" "-m app.main" "%PROJECT_DIR%"
call :install KrossApiGateway "%PYTHON_EXE%" "functions\scripts\api-gateway.py" "%PROJECT_DIR%"
call :install KrossFirebaseEmulator "%NPM_CMD%" "--prefix functions run dev:emulator" "%PROJECT_DIR%"
call :install KrossCloudflareTunnel "%CLOUDFLARED_EXE%" "tunnel run kross-api" "%PROJECT_DIR%"

echo.
echo Services installed and started.
echo Check: sc query KrossReplay
echo Logs: %PROJECT_DIR%\logs\
exit /b 0

:install
set SERVICE=%~1
set APP=%~2
set ARGS=%~3
set DIR=%~4
"%NSSM_EXE%" stop "%SERVICE%" >nul 2>&1
"%NSSM_EXE%" remove "%SERVICE%" confirm >nul 2>&1
"%NSSM_EXE%" install "%SERVICE%" "%APP%" %ARGS%
"%NSSM_EXE%" set "%SERVICE%" AppDirectory "%DIR%"
"%NSSM_EXE%" set "%SERVICE%" AppStdout "%DIR%\logs\%SERVICE%.log"
"%NSSM_EXE%" set "%SERVICE%" AppStderr "%DIR%\logs\%SERVICE%.log"
"%NSSM_EXE%" set "%SERVICE%" AppRotateFiles 1
"%NSSM_EXE%" set "%SERVICE%" AppRotateBytes 10485760
"%NSSM_EXE%" set "%SERVICE%" Start SERVICE_AUTO_START
"%NSSM_EXE%" start "%SERVICE%"
exit /b 0
