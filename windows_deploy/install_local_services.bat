@echo off
setlocal
REM Run as Administrator. Tool paths are resolved from PATH; override any of
REM them below if a tool lives somewhere else on this machine.

set PROJECT_DIR=C:\KrossReplay\cameraSystem
set PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe
set NPM_CMD=C:\Program Files\nodejs\npm.cmd
set CLOUDFLARED_CONFIG=%USERPROFILE%\.cloudflared\config.yml
for /f "delims=" %%i in ('where nssm 2^>nul') do if not defined NSSM_EXE set "NSSM_EXE=%%i"
for /f "delims=" %%i in ('where cloudflared 2^>nul') do if not defined CLOUDFLARED_EXE set "CLOUDFLARED_EXE=%%i"

if not exist "%NSSM_EXE%" echo ERROR: NSSM not found & exit /b 1
if not exist "%PYTHON_EXE%" echo ERROR: Python venv not found & exit /b 1
if not exist "%NPM_CMD%" echo ERROR: npm not found & exit /b 1
if not exist "%CLOUDFLARED_EXE%" echo ERROR: cloudflared not found & exit /b 1
if not exist "%CLOUDFLARED_CONFIG%" echo ERROR: %CLOUDFLARED_CONFIG% not found & exit /b 1
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

REM Services run as LocalSystem, which does not see this user's PATH
REM (ffmpeg, mediamtx, firebase, java), so hand it the current PATH.
set "SERVICE_PATH=%PATH%"

call :install KrossFirebaseEmulator "%NPM_CMD%" "--prefix functions run dev:emulator" "%PROJECT_DIR%"
call :install KrossReplay "%PYTHON_EXE%" "-m app.main" "%PROJECT_DIR%"
call :install KrossApiGateway "%PYTHON_EXE%" "functions\scripts\api-gateway.py" "%PROJECT_DIR%"
call :install KrossCloudflareTunnel "%CLOUDFLARED_EXE%" "--config ""%CLOUDFLARED_CONFIG%"" tunnel run kross-api" "%PROJECT_DIR%"

REM Boot order: emulator -> app -> gateway -> tunnel
"%NSSM_EXE%" set KrossReplay DependOnService KrossFirebaseEmulator
"%NSSM_EXE%" set KrossApiGateway DependOnService KrossReplay
"%NSSM_EXE%" set KrossCloudflareTunnel DependOnService KrossApiGateway

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
"%NSSM_EXE%" set "%SERVICE%" AppEnvironmentExtra "PATH=%SERVICE_PATH%"
"%NSSM_EXE%" set "%SERVICE%" AppStdout "%DIR%\logs\%SERVICE%.log"
"%NSSM_EXE%" set "%SERVICE%" AppStderr "%DIR%\logs\%SERVICE%.log"
"%NSSM_EXE%" set "%SERVICE%" AppRotateFiles 1
"%NSSM_EXE%" set "%SERVICE%" AppRotateBytes 10485760
"%NSSM_EXE%" set "%SERVICE%" Start SERVICE_AUTO_START
"%NSSM_EXE%" start "%SERVICE%"
exit /b 0
