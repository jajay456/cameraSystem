# วิธีติดตั้ง KROSS Replay บน Windows (สำหรับผู้ใช้งานทั่วไป)

คู่มือนี้สำหรับคนที่ได้รับไฟล์ **`KROSS Replay Setup.exe`** มาแล้ว และแค่
ต้องการติดตั้งเพื่อใช้งาน — ไม่ต้องเขียนโค้ดหรือ build อะไรเอง

*(ถ้าเป็นทีมพัฒนาที่ต้องการสร้างไฟล์ `Setup.exe` นี้ขึ้นมาเอง หรือติดตั้ง
บน macOS ดู `SETUP.th.md` แทน)*

---

## ก่อนติดตั้ง: ของที่ต้องมีในเครื่องก่อน

ตัวติดตั้งนี้ไม่ได้รวมโปรแกรมด้านล่างมาให้ ต้องติดตั้งแยกก่อน 1 ครั้ง
(ถ้าเครื่องนี้เคยติดตั้ง KROSS Replay มาก่อนแล้ว ข้ามขั้นตอนนี้ไปได้เลย)

1. **Python 3.11** — ดาวน์โหลดที่ [python.org](https://www.python.org/downloads/)
   ตอนติดตั้ง **ต้องติ๊กช่อง "Add python.exe to PATH"** ด้วย ไม่งั้นขั้นตอน
   ถัดไปจะหาไม่เจอ
2. **ffmpeg** — ดาวน์โหลดที่ [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
   เลือกแบบ "full" หรือ "essentials" แตกไฟล์ zip ไว้ที่ถาวร (เช่น
   `C:\ffmpeg`) แล้วเพิ่มโฟลเดอร์ `bin` ข้างในเข้า PATH ของเครื่อง
   (พิมพ์ค้นหา "environment variables" ใน Windows → Edit the system
   environment variables → Environment Variables → เลือกตัวแปร `Path` →
   Edit → New → วางพาธของโฟลเดอร์ `bin`)
3. **MediaMTX** — ดาวน์โหลดที่
   [GitHub releases](https://github.com/bluenviron/mediamtx/releases)
   เลือกไฟล์ `windows_amd64.zip` แตกไฟล์ไว้ที่ถาวร แล้วเพิ่มโฟลเดอร์นั้น
   (มี `mediamtx.exe` อยู่ข้างใน) เข้า PATH แบบเดียวกับ ffmpeg
4. **NSSM** — ดาวน์โหลดที่ [nssm.cc](https://nssm.cc/download) แตกไฟล์
   แล้วเพิ่มโฟลเดอร์ `win64` (มี `nssm.exe`) เข้า PATH เหมือนกัน

หลังเพิ่มเข้า PATH ครบแล้ว **ต้องรีสตาร์ทเครื่อง** (หรืออย่างน้อยล็อกเอาต์
แล้วล็อกอินใหม่) ก่อนติดตั้ง เพื่อให้ Windows รู้จักโปรแกรมพวกนี้

---

## ขั้นตอนติดตั้ง

### 1. รันตัวติดตั้ง
คลิกขวาที่ไฟล์ `KROSS Replay Setup.exe` → เลือก **"Run as administrator"**
(ต้องรันแบบแอดมิน ไม่งั้นติดตั้ง Windows Service ไม่ได้)

### 2. ทำตามหน้าจอ
- เลือกโฟลเดอร์ที่จะติดตั้ง (ค่าเริ่มต้นคือ
  `C:\Program Files\KrossReplay\camera_system` ปกติใช้ค่าเริ่มต้านได้เลย)
- ติ๊กช่อง "Create a Desktop shortcut" ถ้าอยากได้ไอคอนบน Desktop
- กด Install แล้วรอสักครู่ — ระหว่างนี้ตัวติดตั้งจะ:
  - ก็อปปี้ไฟล์โปรแกรม
  - ติดตั้งไลบรารีที่จำเป็นผ่านอินเทอร์เน็ต (ต้องต่อเน็ตไว้ตอนนี้ อาจใช้
    เวลา 1-2 นาที)
  - ตั้งค่า Windows Service ชื่อ `KrossReplay` ให้รันอัตโนมัติทุกครั้งที่
    เปิดเครื่อง

### 3. กรอกข้อมูลที่จำเป็น
พอติดตั้งเสร็จ จะมีหน้าต่าง **Notepad เปิดขึ้นมา 2 หน้าต่าง** ให้กรอก:

**หน้าต่างที่ 1 — `.env`** ใส่ข้อมูลตามนี้:
```
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```
(ขอข้อมูล Cloudinary จากทีมพัฒนา/แอดมินระบบ — ใช้บัญชีเดียวกันทุกสาขา)

**หน้าต่างที่ 2 — `config.yaml`** แก้ 2 บรรทัดบนสุดในหัวข้อ `branch:`
```yaml
branch:
  id: "รหัสสาขานี้"        # เช่น onnut / sky / indoor / asoke
  name: "ชื่อสาขานี้"       # เช่น KROSS ONNUT
```

**อย่าลืม:** ต้องเอาไฟล์ `firebase-service-account.json` (ขอจากทีมพัฒนา)
มาวางไว้ที่โฟลเดอร์ที่ติดตั้ง (เช่น
`C:\Program Files\KrossReplay\camera_system\firebase-service-account.json`)
ด้วย — ตัวติดตั้งไม่ได้ใส่ไฟล์นี้ให้อัตโนมัติเพราะเป็นความลับเฉพาะระบบ

บันทึกทั้งสองไฟล์ (Ctrl+S) แล้วปิด Notepad

### 4. รีสตาร์ท service ให้อ่านค่าที่กรอกใหม่
เปิด **Command Prompt แบบ Run as administrator** แล้วพิมพ์:
```
net stop KrossReplay
net start KrossReplay
```
(ค่าที่แก้ใน `.env`/`config.yaml` จะมีผลก็ต่อเมื่อรีสตาร์ท service แล้ว)

### 5. เปิดใช้งาน
ดับเบิลคลิกไอคอน **KROSS Replay** บน Desktop (หรือหาใน Start Menu) จะเห็น
หน้าจอกริดกล้อง — หรือเปิดเบราว์เซอร์ไปที่ `http://localhost:8000` ก็ได้
เหมือนกัน

### 6. เพิ่มกล้อง
กดปุ่ม **+ Add Camera** มุมขวาบน → เลือกคอร์ทที่มีอยู่ หรือสร้างคอร์ทใหม่ →
ใส่ RTSP URL ของกล้อง IP (หรือเลือกกล้องในตัวเครื่องถ้ามี) → กด Add

ทดสอบกดปุ่ม **CAPTURE** ที่การ์ดกล้อง ควรขึ้นข้อความ "captured · claim
XXXX" และคลิปจะไปโผล่ในช่อง Recent Highlights หลังผ่านไปสักครู่

---

## ปัญหาที่พบบ่อย

**หน้าเว็บขึ้น "server unreachable"**
เปิด Command Prompt (ไม่ต้อง admin ก็ได้) พิมพ์ `sc query KrossReplay` เช็คว่า
service รันอยู่ไหม (`STATE` ควรเป็น `RUNNING`) ถ้าไม่รัน ลองสั่ง
`net start KrossReplay` แบบ Run as administrator แล้วดู error ที่ขึ้นมา

**อยากดู log ว่าเกิดอะไรขึ้น**
เปิดไฟล์ `logs\server.log` ในโฟลเดอร์ที่ติดตั้ง ด้วย Notepad

**ปุ่ม capture กดแล้วไม่มีอะไรเกิดขึ้น**
เช็คว่ากรอก `.env` ครบและรีสตาร์ท service แล้ว (ขั้นตอนที่ 3-4 ด้านบน) —
ถ้ายังไม่ได้ทำ คลิปจะถูกตัดแต่ไม่ถูกอัปโหลดขึ้น Cloudinary

## วิธีถอนการติดตั้ง
เปิด **Settings → Apps → Installed apps** ค้นหา "KROSS Replay" แล้วกด
Uninstall (จะหยุดและลบ service ให้อัตโนมัติ) หรือเปิด Start Menu →
โฟลเดอร์ "KROSS Replay" → **Uninstall KROSS Replay**
