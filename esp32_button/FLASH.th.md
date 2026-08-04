# วิธีโปรแกรม ESP32 (อัปโหลดโค้ดปุ่มกด)

ทำตามนี้หลังจากต่อสายปุ่มเข้า ESP32 เสร็จแล้ว (ดู `WIRING.th.md`) —
โค้ดอยู่ที่ `esp32_button/kross_button/kross_button.ino`

---

## 1. ติดตั้ง Arduino IDE
ดาวน์โหลดที่ [arduino.cc/en/software](https://www.arduino.cc/en/software)
(เลือกเวอร์ชัน 2.x) ติดตั้งตามปกติ

## 2. เพิ่มการรองรับบอร์ด ESP32
1. เปิด Arduino IDE → **Arduino IDE → Settings** (Mac) หรือ
   **File → Preferences** (Windows)
2. ช่อง "Additional Boards Manager URLs" ใส่:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. กด OK แล้วไปที่เมนู **Tools → Board → Boards Manager**
4. ค้นหา `esp32` → กด Install ตัวที่ชื่อ **"esp32 by Espressif Systems"**
   (ใช้เวลาสักครู่ ไฟล์ค่อนข้างใหญ่)

## 3. ต่อบอร์ดเข้าคอม
เสียบสาย Micro-USB จาก ESP32 เข้าคอม แล้วเลือก:
- **Tools → Board → esp32 → ESP32 Dev Module**
- **Tools → Port** → เลือกพอร์ตที่ขึ้นมา (Mac จะเป็นชื่อประมาณ
  `/dev/cu.usbserial-XXXX` หรือ `/dev/cu.SLAB_USBtoUART`, Windows จะเป็น
  `COM3`, `COM4` ฯลฯ)

ถ้าไม่เห็นพอร์ตขึ้นมาเลย บอร์ดใช้ชิป **CP2102** ต้องลง driver เพิ่ม —
ดาวน์โหลดที่
[silabs.com CP210x driver](https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers)
ลงแล้วถอด-เสียบสาย USB ใหม่

## 4. เปิดไฟล์โค้ดและกรอกข้อมูล
เปิดไฟล์ `esp32_button/kross_button/kross_button.ino` ใน Arduino IDE
แก้ 6 ค่านี้ที่ด้านบนไฟล์ให้ตรงกับของจริง:

```cpp
const char* WIFI_SSID     = "YOUR_WIFI_NAME";       // ชื่อ WiFi ที่คอร์ท
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";   // รหัส WiFi
const char* SERVER_HOST   = "192.168.1.182";         // IP เครื่อง server
const int   SERVER_PORT   = 8000;                    // ปกติไม่ต้องแก้
const char* COURT_ID      = "court_1";                // รหัสคอร์ทใน config.yaml
const char* BUTTON_TOKEN  = "onnut-court_1-ac8761";  // button_token ของคอร์ทนั้น
```

**หา `SERVER_HOST`**: ดูจากข้อความที่เครื่อง server พิมพ์ตอนเปิด (บรรทัด
"from your phone : http://<IP นี้>:8000/m") — แนะนำตั้ง static IP หรือ DHCP
reservation ให้เครื่องนี้ที่เราเตอร์ ไม่งั้น IP อาจเปลี่ยนได้เวลาปิดเปิด
เราเตอร์ใหม่ แล้วปุ่มจะหาเครื่อง server ไม่เจอ

**หา `COURT_ID` และ `BUTTON_TOKEN`**: เปิดไฟล์ `config.yaml` ที่เครื่อง
server ดูใต้หัวข้อ `courts:` เช่น
```yaml
courts:
  court_1:
    button_token: onnut-court_1-ac8761
```
`COURT_ID` = `court_1`, `BUTTON_TOKEN` = `onnut-court_1-ac8761`

## 5. อัปโหลด
กดปุ่ม **Upload** (ลูกศรชี้ขวา มุมซ้ายบน) รอจนขึ้น "Done uploading"

ถ้าขึ้น error แนว "Failed to connect to ESP32" ให้กดค้างปุ่ม **BOOT**
บนตัวบอร์ด (ปุ่มเล็ก ๆ ติดกับพอร์ต USB ไม่ใช่ปุ่มที่เราต่อเพิ่ม) ระหว่างที่
กด Upload แล้วปล่อยตอนเริ่มเห็น progress ขึ้น (บอร์ดบางรุ่นต้องกดเข้าโหมด
โปรแกรมด้วยมือแบบนี้)

## 6. ทดสอบ
เปิด **Tools → Serial Monitor** (หรือกดไอคอนแว่นขยายมุมขวาบน) ตั้ง baud
rate เป็น **115200** ควรเห็นข้อความ:
```
Connecting to WiFi.....
Connected, IP: 192.168.1.xxx
```
ลองกดปุ่มจริงที่ต่อไว้ ควรเห็น:
```
button pressed -> sending trigger
trigger -> HTTP 200: {"ok":true,"court":"court_1","claimCode":"1234"}
```
และถ้าเปิดหน้าเว็บ dashboard ค้างไว้ (`http://<server-ip>:8000`) จะเห็นการ์ด
คอร์ทนั้นขึ้น "captured · claim 1234" เหมือนกดปุ่มบนหน้าเว็บเองเลย

**ถ้าขึ้น HTTP 403** — token ไม่ตรงกับ `config.yaml`, เช็คว่าพิมพ์
`BUTTON_TOKEN` ถูกตัวอักษรครบ (คัดลอกมาจาก config.yaml ตรง ๆ ดีที่สุด)

**ถ้าขึ้น HTTP 429** — ปกติ ไม่ใช่ error หมายถึงเพิ่งกดไปเมื่อไม่นาน
ยังอยู่ในช่วง cooldown (ค่าเริ่มต้น 50 วินาที ตาม `config.yaml`) รอแล้วกด
ใหม่

**ถ้าขึ้น "trigger failed"** — ต่อ WiFi ได้แต่ยิงหา server ไม่เจอ เช็คว่า
`SERVER_HOST` ถูกต้อง และเครื่อง server เปิดอยู่จริง กับ ESP32/server
อยู่ WiFi วงเดียวกัน

---

## ขั้นต่อไป
ทดสอบผ่านคอร์ทเดียวแล้วโอเค ค่อยทำซ้ำสำหรับคอร์ทอื่น — แค่เปลี่ยน
`COURT_ID` / `BUTTON_TOKEN` ให้ตรงกับคอร์ทนั้น ๆ ใน `config.yaml` (ต้อง
เพิ่มคอร์ทนั้นในระบบก่อนผ่านหน้าเว็บ **+ Add Camera** ถ้ายังไม่มี) แล้ว
อัปโหลดโค้ดชุดใหม่ลง ESP32 ตัวใหม่
