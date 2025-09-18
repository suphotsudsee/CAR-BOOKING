# Quick Start Guide

## 1. ลงทะเบียนหรือเข้าสู่ระบบ
- ผู้ใช้ใหม่สามารถสร้างบัญชีผ่าน `/register` โดยกรอกข้อมูลส่วนตัว เลือกบทบาท (พนักงาน, คนขับ, ผู้ดูแล) และยอมรับนโยบายความปลอดภัย ระบบจะตรวจสอบความถูกต้องของอีเมล รหัสผ่าน และบทบาทก่อนสร้างบัญชี.【F:frontend/src/app/register/page.tsx†L1-L200】
- หากมีบัญชีอยู่แล้ว ให้เข้าสู่ระบบที่ `/login` โดยกรอกชื่อผู้ใช้/อีเมลและรหัสผ่าน จากนั้นเลือกว่าให้จำการเข้าสู่ระบบบนอุปกรณ์ปัจจุบันหรือไม่.【F:frontend/src/app/login/page.tsx†L21-L148】

## 2. ยืนยันโปรไฟล์และบทบาท
หลังล็อกอิน ระบบ AuthContext จะดึงข้อมูลผู้ใช้จาก API พร้อมบทบาทที่ระบุ (requester, manager, fleet_admin, driver, auditor) และสถานะการเปิด 2FA เพื่อปรับประสบการณ์ใช้งานบนแดชบอร์ดอัตโนมัติ.【F:frontend/src/context/AuthContext.tsx†L13-L120】

## 3. สำรวจแดชบอร์ดตามบทบาท
- ระบบมีแดชบอร์ดเฉพาะบทบาท (ผู้ขอใช้รถ, ผู้จัดการ, ผู้ดูแลยานพาหนะ, คนขับ) โดยจะเลือกชุดคอมโพเนนต์ตามบทบาทผู้ใช้ที่ล็อกอิน.【F:frontend/src/app/dashboard/page.tsx†L1-L164】
- ปุ่มด่วนและการ์ดสถิติช่วยนำทางไปยังฟีเจอร์สำคัญ เช่น สร้างคำขอจองรถ อนุมัติคำขอ จัดการรถ/คนขับ หรือเช็กอินงานขับรถตามสิทธิ์ของแต่ละบทบาท.【F:frontend/src/components/dashboard/index.ts†L1-L40】【F:frontend/src/components/dashboard/RequesterDashboard.tsx†L92-L153】

## 4. เรียนรู้ขั้นตอนงานหลัก
| บทบาท | ขั้นตอนแรกที่แนะนำ |
|--------|----------------------|
| Requester | สร้างคำขอแรกผ่านปุ่ม “สร้างคำขอจองรถ” และตรวจสอบประวัติคำขอในตารางด้านล่าง.【F:frontend/src/components/dashboard/RequesterDashboard.tsx†L92-L153】 |
| Manager | เปิดคิวอนุมัติ ตรวจสอบรายละเอียด แล้วใช้ปุ่ม “ตรวจสอบคำขอทั้งหมด” เพื่อเข้าถึงรายการเต็มและอนุมัติ/ปฏิเสธผ่าน API.【F:frontend/src/components/dashboard/ManagerDashboard.tsx†L109-L197】【F:backend/app/api/api_v1/endpoints/bookings.py†L118-L343】 |
| Fleet Admin | เพิ่มรถคันแรก ตรวจสอบสถานะและกำหนดการบำรุงรักษา พร้อมจัดการเอกสารผ่านเมนูด่วน.【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L125-L199】【F:backend/app/api/api_v1/endpoints/vehicles.py†L50-L200】 |
| Driver | อ่านตารางงานประจำวัน กดเช็กอินก่อนออกเดินทาง และเช็กเอาต์เมื่อเสร็จงานเพื่อบันทึกข้อมูลครบถ้วน.【F:frontend/src/components/dashboard/DriverDashboard.tsx†L74-L219】【F:backend/app/api/api_v1/endpoints/job_runs.py†L200-L258】 |

## 5. ตั้งค่าการแจ้งเตือนและความปลอดภัย
- ระบบรองรับการแจ้งเตือนในแอป (และช่องทางอื่นตามนโยบาย) เมื่อมีการอนุมัติ/ปฏิเสธหรืออัปเดตสถานะคำขอ โดยข้อมูลเก็บในโมดูล Notification.【F:backend/app/api/api_v1/endpoints/bookings.py†L58-L83】【F:backend/app/models/notification.py†L1-L48】
- ผู้ดูแลควรบังคับใช้นโยบายความปลอดภัย เช่น 2FA และรหัสผ่านตามข้อกำหนดที่หน้า register รวมถึงตรวจสอบสิทธิ์ใน `system_configurations` เพื่อจำกัดจำนวนคำขอค้างต่อผู้ใช้.【F:frontend/src/app/register/page.tsx†L181-L189】【F:backend/app/models/system.py†L14-L58】

## 6. ขยายการใช้งาน
- เชื่อมต่อ API ผ่าน `docs/system/api/openapi.json` หรือ Swagger UI เพื่อผสานระบบอื่น เช่น ระบบ HR หรือจองห้องประชุม.【F:docs/system/api/README.md†L1-L40】
- ใช้รายงานและปฏิทินในแดชบอร์ดเพื่อติดตามแนวโน้มและวางแผนการใช้รถขององค์กรอย่างมีประสิทธิภาพ.【F:frontend/src/components/dashboard/ManagerDashboard.tsx†L128-L197】【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L150-L199】
