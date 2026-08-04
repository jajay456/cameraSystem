# KROSS Replay — คู่มือติดตั้ง (เริ่มจากเครื่องเปล่า)

คู่มือนี้ครอบคลุมทุกขั้นตอนตั้งแต่เครื่องที่ยังไม่มีอะไรติดตั้งเลย จนรัน
KROSS Replay ได้ ทั้งบน **macOS** และ **Windows** — เลือกอ่านหัวข้อของ OS
ที่ใช้

ครอบคลุม: ติดตั้งโปรแกรมที่จำเป็น → เอาโปรเจกต์มาไว้ในเครื่อง → ตั้งค่า →
รันเช็คด้วยมือ → ตั้งให้รันอัตโนมัติตอนเปิดเครื่อง → (ทางเลือก) แอพเดสก์ท็อป/tray
icon ที่ดับเบิลคลิกเปิดได้เลย

*(English version: [SETUP.md](SETUP.md))*

*(เป็นผู้ใช้งานทั่วไปบน Windows ที่มีไฟล์ `KROSS Replay Setup.exe` แล้ว
และแค่อยากติดตั้งใช้งาน ไม่ต้อง build เอง? ดู [INSTALL.th.md](INSTALL.th.md)
แทน — สั้นและง่ายกว่านี้มาก)*

---

## macOS

### 1. ติดตั้งโปรแกรมที่จำเป็น
เปิด Terminal

ถ้ายังไม่มี [Homebrew](https://brew.sh) ให้ติดตั้งก่อน:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

จากนั้นติดตั้งเครื่องมือที่โปรเจกต์นี้ต้องใช้:
```bash
brew install python@3.11 ffmpeg mediamtx
```

### 2. เอาโปรเจกต์มาไว้ในเครื่อง
ถ้ากำลังตั้งค่า **สาขา/สถานที่ใหม่** ให้ก็อปปี้โฟลเดอร์ `camera_system`
ทั้งโฟลเดอร์จากเครื่องเดิม (ผ่าน AirDrop, USB ฯลฯ) **รวมถึง** `.env` และ
`firebase-service-account.json` ด้วย — ข้อมูลรับรองพวกนี้ใช้ร่วมกันทุกสาขา
โดยตั้งใจ (ดูรายละเอียดใน `MULTI_BRANCH.md`) **ห้าม** ก็อปโฟลเดอร์ `.venv`
มาด้วย เดี๋ยวสร้างใหม่ในขั้นตอนถัดไป

ถ้าเริ่มจากศูนย์จริง ๆ (ไม่มีสาขาเดิมให้ก็อป) ให้วางโฟลเดอร์โปรเจกต์ไว้ที่
เช่น `~/Documents/camera_system` แล้วค่อยกรอกข้อมูลใน `.env` เองในขั้นตอนที่ 4

### 3. ตั้งค่า Python environment
```bash
cd ~/Documents/camera_system
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 4. ตั้งค่าข้อมูลรับรองและตัวตนของสาขานี้
```bash
cp .env.example .env
```
แก้ไฟล์ `.env` กรอก:
- `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` —
  ดูได้จาก Cloudinary dashboard (ไว้อัปโหลดวิดีโอคลิป)
- `FIREBASE_SERVICE_ACCOUNT_PATH` — ปล่อยเป็น `./firebase-service-account.json`
  แล้วเอาไฟล์นี้ (ดาวน์โหลดจาก Firebase Console → Project Settings →
  Service Accounts → Generate new private key) มาวางไว้ที่ root ของโปรเจกต์

ถ้าเครื่องนี้เป็น **สาขา/สถานที่ใหม่** ไม่ใช่ก็อปมาจากสาขาเดิม ให้แก้
`config.yaml` เพิ่มด้วย:
- `branch.id` / `branch.name` — รหัสสั้น ๆ ที่ไม่ซ้ำใคร กับชื่อที่ใช้แสดงผล
- `cameras: []` และ `courts: {}` — ล้างของเดิมออก แล้วค่อยเพิ่มกล้องจริง
  ผ่านหน้าเว็บทีหลัง ด้วยปุ่ม **+ Add Camera**

### 5. รันด้วยมือเพื่อเช็คก่อน
```bash
.venv/bin/python -m app.main
```
ควรเห็นข้อความพิมพ์ `http://localhost:8000` ออกมา เปิดลิงก์นั้นในเบราว์เซอร์
— ควรเห็นหน้ากริดกล้อง (การ์ดคอร์ท ปุ่ม CAPTURE) กด `Ctrl+C` เพื่อหยุด
เมื่อเช็คผ่านแล้ว

### 6. ตั้งให้รันอัตโนมัติ (launchd service)
ไฟล์ `com.kross.replay.plist` ตั้งค่าไว้ให้รันเซิร์ฟเวอร์ผ่าน `launchd`
อยู่แล้ว (รันตอนล็อกอิน รีสตาร์ทเองถ้า crash) ถ้าเป็นการก็อปมาไว้เครื่องใหม่
ให้เช็คพาธในไฟล์นี้ว่าตรงกับตำแหน่งโปรเจกต์บนเครื่องนี้จริงก่อน แล้วรัน:
```bash
cp com.kross.replay.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.kross.replay.plist
```
เช็คว่ารันอยู่ไหม: `launchctl list | grep kross` — ดู log ได้ที่ `logs/server.log`

### 7. ทางเลือก: ไอคอน menu bar คุมเซิร์ฟเวอร์
`control_app/kross_control.py` เป็นไอคอนบน menu bar (เขียว/แดงบอกสถานะ)
มีปุ่ม Start/Stop/Open Dashboard/View Logs คุม service จากข้อ 6
```bash
.venv/bin/pip install rumps py2app pyobjc
cd control_app
../.venv/bin/python setup.py py2app
```
จะได้ `control_app/dist/KROSS Control.app` — ลากไปไว้ที่ `/Applications`
แล้วเพิ่มเข้า Login Items (System Settings → General → Login Items)
เพื่อให้ไอคอนขึ้นบน menu bar ทุกครั้งที่เปิดเครื่อง

### 8. ทางเลือก: แอพหน้าต่าง dashboard + ไอคอนบน Desktop
`desktop_app/kross_dashboard.py` เปิดหน้า dashboard (กริดกล้อง) เป็น
หน้าต่างแอพแยกของตัวเอง แทนที่จะเปิดใน browser tab และจะสั่งรันเซิร์ฟเวอร์
ให้เองถ้ายังไม่ทำงานอยู่
```bash
.venv/bin/pip install pywebview
cd desktop_app
../.venv/bin/python setup.py py2app
```
จะได้ `desktop_app/dist/KROSS Replay.app` — ก็อปไปไว้ที่ Desktop
เพื่อให้เป็นไอคอนดับเบิลคลิกเปิดได้เลย:
```bash
cp -R "dist/KROSS Replay.app" ~/Desktop/
```
ทุกครั้งที่แก้ `kross_dashboard.py` ต้อง build ใหม่แล้วก็อปทับที่ Desktop อีกรอบ

---

## Windows

ขั้นตอนด้านล่างนี้เขียนสำหรับเครื่อง Windows เปล่า **ยังไม่เคยรันทดสอบบน
เครื่อง Windows จริง** (เขียนจาก macOS ซึ่งรันหรือ build ไฟล์ Windows
ให้ไม่ได้) — ถ้าขั้นตอนไหน error ให้จดข้อความ error ที่ขึ้นมาไว้เพื่อแก้ต่อ

### 1. ติดตั้งโปรแกรมที่จำเป็น
- [Python 3.11](https://www.python.org/downloads/) — ตอนติดตั้งให้ติ๊ก
  **"Add python.exe to PATH"** ด้วย
- [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) — ดาวน์โหลดแบบ "full" หรือ
  "essentials" แตกไฟล์ไว้ที่ถาวร (เช่น `C:\ffmpeg`) แล้วเพิ่มโฟลเดอร์ `bin`
  ของมันเข้า PATH (ค้นหา "environment variables" ใน Settings → Edit ตัวแปร
  `Path` → New → วางพาธของโฟลเดอร์ `bin`)
- [MediaMTX](https://github.com/bluenviron/mediamtx/releases) — ดาวน์โหลด
  zip แบบ `windows_amd64` แตกไฟล์ (มี `mediamtx.exe` อยู่ข้างใน) แล้วเพิ่ม
  เข้า PATH เหมือน ffmpeg
- [NSSM](https://nssm.cc/download) — แตกไฟล์ จดพาธของ `nssm.exe` (ใช้โฟลเดอร์
  `win64`) — ใช้แค่ตอนตั้งค่าให้รันอัตโนมัติ (ข้อ 6)

### 2. เอาโปรเจกต์มาไว้ในเครื่อง
ก็อปโฟลเดอร์ `camera_system` ทั้งหมดมาไว้ที่เครื่องนี้ เช่น
`C:\KrossReplay\camera_system` ถ้าเป็นสาขาใหม่ที่ก็อปมาจากสาขาเดิม ให้เอา
`.env` กับ `firebase-service-account.json` มาด้วยเลย (ข้อมูลรับรองใช้ร่วมกัน
ทุกสาขา — ดู `MULTI_BRANCH.md`) **ห้าม** ก็อปโฟลเดอร์ `.venv` มาด้วย

### 3. ตั้งค่า Python environment
เปิด PowerShell:
```powershell
cd C:\KrossReplay\camera_system
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 4. ตั้งค่าข้อมูลรับรองและตัวตนของสาขานี้
```powershell
copy .env.example .env
```
กรอก `.env` เหมือนหัวข้อ macOS ด้านบน (Cloudinary keys, พาธไฟล์ Firebase
service account) เอาไฟล์ `firebase-service-account.json` มาวางไว้ที่ root
ของโปรเจกต์ถ้ายังไม่มี

ถ้าเป็น **สาขา/สถานที่ใหม่** ให้แก้ `config.yaml` เพิ่มด้วย:
- `branch.id` / `branch.name` — รหัสและชื่อของสาขานี้
- `system.encoder` → ตั้งเป็น `libx264` (ค่าปลอดภัยสุด ใช้ได้แม้ไม่มีการ์ดจอ
  พิเศษ — ดูคอมเมนต์ใน `config.yaml` สำหรับตัวเลือก `qsv` ถ้าเครื่องนี้มี
  Intel iGPU รุ่นใหม่)
- ล้างข้อมูลทดสอบออก: `cameras: []`, `courts: {}` ใน `config.yaml` และ
  `paths: {}` ใน `mediamtx.yml` (เก็บ `api: yes` ไว้)

### 5. รันด้วยมือเพื่อเช็คก่อน
```powershell
.venv\Scripts\python -m app.main
```
เปิด `http://localhost:8000` ในเบราว์เซอร์ — ควรเห็นหน้ากริดกล้อง ใช้ปุ่ม
**+ Add Camera** เพื่อเพิ่มกล้องจริงของสาขานี้ ลองกด capture → ตัดคลิป →
อัปขึ้น Cloudinary → บันทึก Firestore ให้ผ่านก่อนไปขั้นถัดไป กด `Ctrl+C`
เพื่อหยุด

### 6. ตั้งให้รันอัตโนมัติ (Windows Service ผ่าน NSSM)
แก้ `NSSM_EXE` กับ `PROJECT_DIR` ที่ด้านบนของไฟล์
`windows_deploy\install_service.bat` ให้ตรงกับเครื่องนี้ แล้วคลิกขวา →
**Run as administrator**

จะได้ service ชื่อ `KrossReplay` ที่รันตอนบูตเครื่อง (แม้ยังไม่ล็อกอิน)
และรีสตาร์ทเองถ้า crash เช็คสถานะด้วย `sc query KrossReplay` — ดู log ได้ที่
`logs\server.log` ลบทีหลังได้ด้วยการแก้แล้วรัน
`windows_deploy\uninstall_service.bat` แบบ administrator

### 7. ทางเลือก: ไอคอน tray คุมเซิร์ฟเวอร์
`windows_deploy\kross_control_win.py` เป็นไอคอนบน system tray
(เขียว/แดงบอกสถานะ) มีปุ่ม Start/Stop/Open Dashboard/View Logs คุม service
จากข้อ 6
```powershell
pip install -r windows_deploy\requirements.txt
python windows_deploy\kross_control_win.py
```
build เป็น `.exe` ดับเบิลคลิกเปิดได้:
```powershell
cd windows_deploy
pyinstaller --onefile --windowed --name "KROSS Control" kross_control_win.py
```
ไฟล์ `.exe` จะอยู่ที่ `windows_deploy\dist\KROSS Control.exe` — สร้าง
shortcut ไว้ในโฟลเดอร์ Startup (`Win+R` → `shell:startup`) ให้ไอคอนขึ้น
อัตโนมัติตอนล็อกอิน

**หมายเหตุ:** ปุ่ม Start/Stop ในแอพ tray ต้องใช้สิทธิ์ admin (เรียก `net
start`/`net stop`) — ถ้ากดแล้วไม่มีอะไรเกิดขึ้น ให้รันแอพ tray แบบ
Administrator

### 8. ทางเลือก: แอพหน้าต่าง dashboard + ไอคอนบน Desktop
`desktop_app\kross_dashboard_win.py` เปิดหน้า dashboard เป็นหน้าต่างแอพแยก
ของตัวเอง ต่างจากแอพ tray ตรงที่มันไม่ได้คุม service โดยตรง แค่สั่งเริ่ม
ให้ถ้ายังไม่ทำงาน (`net start KrossReplay`) ปิดหน้าต่างแล้ว service
ไม่หยุดตาม
```powershell
pip install -r requirements.txt
pip install -r windows_deploy\requirements.txt
cd desktop_app
pyinstaller --onefile --windowed --name "KROSS Replay" kross_dashboard_win.py
```
ไฟล์ `.exe` จะอยู่ที่ `desktop_app\dist\KROSS Replay.exe` — ก็อปไปไว้ที่
Desktop เพื่อให้เป็นไอคอนดับเบิลคลิกเปิดได้เลย หรือสร้าง shortcut ไว้ใน
โฟลเดอร์ Startup ให้เปิดอัตโนมัติตอนล็อกอิน

### 9. ทางเลือก: ข้ามขั้นตอน 3–8 ด้วยตัวติดตั้งจริง
`windows_deploy\installer\kross_replay.iss` รวมทุกอย่างด้านบน (venv,
ติดตั้ง dependencies, service `KrossReplay`, แอพเดสก์ท็อปทั้งสอง +
shortcut) ไว้ในไฟล์เดียว `KROSS Replay Setup.exe` ยังต้องมี
Python/ffmpeg/MediaMTX/NSSM จากขั้นตอนที่ 1 ติดตั้งไว้ก่อนอยู่ดี ดูวิธี
build และรายละเอียดว่า bundle อะไรบ้าง/ไม่ bundle อะไรบ้างได้ที่
`windows_deploy/README.md` ข้อ 9

---

## ขั้นตอนถัดไปที่ใช้ร่วมกัน (ทั้งสอง OS)
- **เพิ่มกล้อง**: เปิดหน้า dashboard → **+ Add Camera** → เลือกคอร์ทที่มีอยู่
  หรือสร้างใหม่ → ใส่ RTSP URL (กล้อง IP) หรือเลือกกล้องในตัวเครื่อง
  Mac/Windows
- **หลายสาขา**: ดู `MULTI_BRANCH.md` สำหรับวิธีใช้ Cloudinary + Firebase
  บัญชีเดียวรองรับหลายสถานที่แยกกันอิสระ
- **แก้ปัญหาเบื้องต้น**: เช็ค `logs/server.log` ก่อนเป็นอันดับแรก ถ้าหน้า
  dashboard ขึ้น "server unreachable" ให้เช็คว่า process เซิร์ฟเวอร์
  (รันด้วยมือ, launchd service, หรือ Windows service) ทำงานอยู่จริง และ
  ไม่มีอย่างอื่นใช้ port 8000 อยู่ก่อนแล้ว
