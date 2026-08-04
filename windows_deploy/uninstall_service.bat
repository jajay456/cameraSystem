@echo off
REM Removes the KrossReplay Windows Service (installed by install_service.bat).
REM Right-click -> "Run as administrator".

set NSSM_EXE=C:\nssm\nssm.exe
set SERVICE_NAME=KrossReplay

"%NSSM_EXE%" stop %SERVICE_NAME%
"%NSSM_EXE%" remove %SERVICE_NAME% confirm

echo Done. Service "%SERVICE_NAME%" removed.
