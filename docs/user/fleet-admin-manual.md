# ผู้ดูแลยานพาหนะ (Fleet Admin) – คู่มือการใช้งาน

## ภาพรวมบทบาท
ผู้ดูแลยานพาหนะรับผิดชอบการบริหารจัดการรถยนต์ คนขับ และกำหนดการบำรุงรักษา ระบบแสดงสถิติภาพรวม เช่น อัตราการใช้งาน รถที่ไม่พร้อมให้บริการ งานซ่อม และระดับน้ำมันในแดชบอร์ดเพื่อช่วยตัดสินใจได้รวดเร็ว.【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L40-L123】

## การจัดการรถยนต์
1. ใช้ปุ่มด่วน **“เพิ่มรถคันใหม่”** เพื่อกรอกข้อมูลรถและลงทะเบียนอุปกรณ์ติดตามในระบบ.【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L174-L199】
2. ตรวจสอบสถานะรถจากรายการ “รายการยานพาหนะและทรัพยากร” เพื่อดูว่ารถพร้อมใช้งาน อยู่ระหว่างซ่อม หรือมีการแจ้งเตือนจาก IoT พร้อมผู้รับผิดชอบ.【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L125-L147】
3. ในฝั่ง API สามารถเรียก `/api/v1/vehicles` เพื่อค้นหา/กรองรถตามสถานะ ประเภท หรือคำค้น รวมถึงอัปเดตข้อมูลและเอกสารประกอบผ่านเอ็นด์พอยต์ที่เกี่ยวข้อง.【F:backend/app/api/api_v1/endpoints/vehicles.py†L50-L200】
4. ฟีเจอร์ “จัดตารางบำรุงรักษา” จะเชื่อมกับปฏิทินและรายการบำรุงรักษาที่แสดงด้านล่างเพื่อวางแผนเชิงรุก.【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L150-L199】

## การบริหารคนขับ
- เรียกดูหรืออัปเดตข้อมูลคนขับผ่านแดชบอร์ดคนขับ หรือใช้ API `/api/v1/drivers` สำหรับสร้าง แก้ไข สถานะ/ตารางการทำงาน และแจ้งเตือนวันหมดอายุใบขับขี่.【F:backend/app/api/api_v1/endpoints/drivers.py†L40-L200】
- ใช้ปุ่มด่วน “ติดตาม GPS” เพื่อตรวจสอบตำแหน่งรถและงานปัจจุบันผ่านระบบติดตาม (หากผสานกับฮาร์ดแวร์).【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L174-L199】

## การติดตามบำรุงรักษาและเอกสาร
- ตาราง “กำหนดการบำรุงรักษา” แสดงงานซ่อม/ตรวจเช็กตามรถและสถานะ (Scheduled, Completed, Pending) เพื่อจัดสรรทีมช่างและอะไหล่.【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L150-L171】
- ใช้ API `/api/v1/vehicles/document-expiry` เพื่อรับการแจ้งเตือนเอกสารหมดอายุล่วงหน้า พร้อมลิงก์ไฟล์ที่จัดเก็บไว้ใน `uploads/`.【F:backend/app/api/api_v1/endpoints/vehicles.py†L76-L97】【F:backend/app/core/config.py†L29-L41】

## การวิเคราะห์และรายงาน
- ปุ่ม “วิเคราะห์การใช้งาน” เปิดรายงานเชิงลึกเกี่ยวกับการใช้รถ เพื่อประเมินประสิทธิภาพและหาแนวทางเพิ่มการใช้ทรัพยากร.【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L174-L199】
- สถิติบนแดชบอร์ดช่วยประเมิน KPI เช่น อัตราการใช้งาน (Utilisation), จำนวนรถที่ไม่พร้อม, งานบำรุงรักษา, และค่าเชื้อเพลิงเฉลี่ย.【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L92-L123】

## แนวทางปฏิบัติที่ดี
- อัปเดตสถานะรถและบันทึกการบำรุงรักษาทันทีที่มีการเปลี่ยนแปลงเพื่อลดการชนกับงานจอง.【F:backend/app/api/api_v1/endpoints/vehicles.py†L128-L170】
- กำหนดตรวจสอบใบขับขี่และเอกสารรถประจำสัปดาห์โดยเรียกดูรายการหมดอายุล่วงหน้า เพื่อป้องกันความเสี่ยงด้านกฎหมาย.【F:backend/app/api/api_v1/endpoints/vehicles.py†L76-L97】【F:backend/app/api/api_v1/endpoints/drivers.py†L175-L200】
