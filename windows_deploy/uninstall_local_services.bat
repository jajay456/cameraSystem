@echo off
setlocal
set NSSM_EXE=C:\nssm\nssm.exe
for %%S in (KrossCloudflareTunnel KrossApiGateway KrossReplay KrossFirebaseEmulator) do (
  "%NSSM_EXE%" stop %%S >nul 2>&1
  "%NSSM_EXE%" remove %%S confirm >nul 2>&1
)
echo Local KROSS services removed.
