; KROSS Replay — Windows installer (Inno Setup script)
;
; NOT YET TESTED ON WINDOWS — written from macOS, same as the rest of
; windows_deploy/. Build and run this on a real Windows machine, and
; report back any errors so they can be fixed.
;
; What this installer does (the "lightweight" scope — it does NOT bundle
; Python/ffmpeg/MediaMTX/NSSM themselves; those must already be installed
; and on PATH, per SETUP.md's Windows section):
;   1. Copies the project source (app/, web/, assets/, requirements.txt,
;      config.yaml, mediamtx.yml) to the install folder — NOT .env or
;      firebase-service-account.json, since those are secrets/site-specific
;      and must be filled in after install (the installer copies
;      .env.example -> .env as a starting point and opens both files in
;      Notepad at the end so they're easy to fill in).
;   2. Creates a fresh venv and runs `pip install -r requirements.txt`
;      (needs internet access during install).
;   3. Registers the "KrossReplay" auto-starting Windows Service via NSSM
;      (same setup as install_service.bat, just scripted).
;   4. Installs the pre-built KROSS Replay.exe (dashboard window) and
;      KROSS Control.exe (tray icon) with Start Menu + Desktop shortcuts.
;   5. Uninstalling stops and removes the Windows Service too.
;
; ---- Build steps (run ON Windows, in this order) ----
;   1. Build the two desktop apps first (PyInstaller, must run on Windows):
;        cd desktop_app
;        pyinstaller --onefile --windowed --name "KROSS Replay" ^
;          --icon "..\assets\icon\KROSSReplay.ico" kross_dashboard_win.py
;        cd ..\windows_deploy
;        pyinstaller --onefile --windowed --name "KROSS Control" ^
;          --icon "..\assets\icon\KROSSReplay.ico" kross_control_win.py
;   2. Install Inno Setup: https://jrsoftware.org/isinfo.php
;   3. Right-click this file -> Compile (or run
;        ISCC.exe windows_deploy\installer\kross_replay.iss
;      from a Developer/regular command prompt with Inno Setup on PATH)
; Output: windows_deploy\installer\Output\KROSS Replay Setup.exe

#define MyAppName "KROSS Replay"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "KROSS"
#define MyServiceName "KrossReplay"

[Setup]
AppId={{9F3B9A0E-6C2D-4C0D-A5A0-KROSSREPLAY1}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\KrossReplay\camera_system
DefaultGroupName=KROSS Replay
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=KROSS Replay Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
SetupIconFile=..\..\assets\icon\KROSSReplay.ico
UninstallDisplayIcon={app}\KROSS Replay.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut for KROSS Replay"; GroupDescription: "Additional icons:"

[Files]
; project source the server needs to run — deliberately excludes .env,
; firebase-service-account.json, .venv, logs, buffer, clips (secrets and
; machine-specific/runtime state, never shipped in an installer)
Source: "..\..\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\web\*"; DestDir: "{app}\web"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\.env.example"; DestDir: "{app}"; Flags: ignoreversion
; config.yaml / mediamtx.yml: only placed if this is a fresh install (never
; overwrite an existing site's config on upgrade/reinstall)
Source: "..\..\config.yaml"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "..\..\mediamtx.yml"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "..\install_service.bat"; DestDir: "{app}\windows_deploy"; Flags: ignoreversion
Source: "..\uninstall_service.bat"; DestDir: "{app}\windows_deploy"; Flags: ignoreversion
; pre-built desktop apps — build these first, see header comment above
Source: "..\..\desktop_app\dist\KROSS Replay.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\KROSS Control.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\KROSS Replay"; Filename: "{app}\KROSS Replay.exe"
Name: "{group}\KROSS Control"; Filename: "{app}\KROSS Control.exe"
Name: "{group}\Uninstall KROSS Replay"; Filename: "{uninstallexe}"
Name: "{autodesktop}\KROSS Replay"; Filename: "{app}\KROSS Replay.exe"; Tasks: desktopicon

[Run]
; --- Python environment ---
Filename: "python"; Parameters: "-m venv "".venv"""; WorkingDir: "{app}"; StatusMsg: "Setting up Python environment..."; Flags: runhidden
Filename: "{app}\.venv\Scripts\pip.exe"; Parameters: "install -r requirements.txt"; WorkingDir: "{app}"; StatusMsg: "Installing dependencies (needs internet)..."; Flags: runhidden

; --- starter .env so the service has something to load (still needs real
;     credentials filled in — see the Notepad windows opened below) ---
Filename: "{cmd}"; Parameters: "/c if not exist ""{app}\.env"" copy ""{app}\.env.example"" ""{app}\.env"""; Flags: runhidden

; --- register the auto-starting Windows Service (mirrors install_service.bat) ---
Filename: "nssm"; Parameters: "install {#MyServiceName} ""{app}\.venv\Scripts\python.exe"" ""-m app.main"""; StatusMsg: "Registering KrossReplay service..."; Flags: runhidden
Filename: "nssm"; Parameters: "set {#MyServiceName} AppDirectory ""{app}"""; Flags: runhidden
Filename: "nssm"; Parameters: "set {#MyServiceName} AppStdout ""{app}\logs\server.log"""; Flags: runhidden
Filename: "nssm"; Parameters: "set {#MyServiceName} AppStderr ""{app}\logs\server.log"""; Flags: runhidden
Filename: "nssm"; Parameters: "set {#MyServiceName} AppRotateFiles 1"; Flags: runhidden
Filename: "nssm"; Parameters: "set {#MyServiceName} AppRotateBytes 10485760"; Flags: runhidden
Filename: "nssm"; Parameters: "set {#MyServiceName} Start SERVICE_AUTO_START"; Flags: runhidden
Filename: "nssm"; Parameters: "start {#MyServiceName}"; StatusMsg: "Starting KrossReplay service..."; Flags: runhidden

; --- open the two files that still need real values, so setup isn't
;     "done" with the server silently missing credentials ---
Filename: "notepad.exe"; Parameters: """{app}\.env"""; Description: "Open .env to fill in R2/Firebase credentials"; Flags: postinstall skipifsilent nowait
Filename: "notepad.exe"; Parameters: """{app}\config.yaml"""; Description: "Open config.yaml to set this branch's id/name"; Flags: postinstall skipifsilent nowait unchecked
Filename: "{app}\KROSS Replay.exe"; Description: "Launch KROSS Replay now"; Flags: postinstall skipifsilent nowait unchecked

[UninstallRun]
Filename: "nssm"; Parameters: "stop {#MyServiceName}"; Flags: runhidden
Filename: "nssm"; Parameters: "remove {#MyServiceName} confirm"; Flags: runhidden
