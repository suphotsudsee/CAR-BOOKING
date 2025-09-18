# FAQ & Common Issues

### Q1: ลืมรหัสผ่านต้องทำอย่างไร?
ไปที่ `/reset-password` เลือกรับลิงก์ทางอีเมลหรือรหัส OTP ผ่าน SMS ตามที่ผูกไว้กับบัญชี ระบบจะจำกัดความถี่การรีเซ็ตและบันทึกประวัติไว้เพื่อความปลอดภัย.【F:frontend/src/app/reset-password/page.tsx†L1-L130】

### Q2: จะเปิดหรือปิดการยืนยันตัวตนสองขั้นตอน (2FA) ได้อย่างไร?
เปิดหน้าโปรไฟล์แล้วติ๊กสวิตช์ “เปิดใช้งานการยืนยันตัวตนสองขั้นตอน” จากนั้นบันทึกการเปลี่ยนแปลง ระบบ AuthContext จะอัปเดตสถานะและใช้ในการตรวจสอบตอนเข้าสู่ระบบครั้งถัดไป.【F:frontend/src/app/profile/page.tsx†L24-L200】【F:frontend/src/context/AuthContext.tsx†L13-L120】

### Q3: ทำไมฉันจึงไม่เห็นคำขอของเพื่อนร่วมทีม?
ผู้ขอใช้รถสามารถเข้าถึงเฉพาะคำขอของตนเองผ่าน `/api/v1/bookings/me` หากต้องการดูคำขอทั้งหมดต้องมีบทบาทผู้จัดการหรือผู้ดูแลยานพาหนะ ซึ่งจะใช้ `/api/v1/bookings` ที่จำกัดสิทธิ์ด้วย Role-Based Access.【F:backend/app/api/api_v1/endpoints/bookings.py†L118-L199】

### Q4: ระบบแจ้งว่า “Directory 'uploads' does not exist” เมื่อเปิดเซิร์ฟเวอร์?
ต้องสร้างโฟลเดอร์ `uploads/` (หรือแมป volume) ก่อนเริ่มต้นแอป เพราะ FastAPI จะ mount โฟลเดอร์นี้เพื่อให้บริการไฟล์สื่อ/เอกสารผ่าน `/static` เสมอ.【F:backend/app/core/config.py†L29-L41】【F:backend/app/main.py†L21-L88】

### Q5: จะตรวจสอบสถานะเอกสารรถหรือใบขับขี่ที่กำลังจะหมดอายุได้อย่างไร?
ผู้ดูแลยานพาหนะสามารถเรียก API `/api/v1/vehicles/document-expiry` และ `/api/v1/drivers/license-expiry` เพื่อดึงรายการที่หมดอายุภายในระยะเวลาที่กำหนด พร้อมลิงก์ไฟล์ประกอบ.【F:backend/app/api/api_v1/endpoints/vehicles.py†L76-L97】【F:backend/app/api/api_v1/endpoints/drivers.py†L175-L200】

### Q6: ช่องทางแจ้งเตือนรองรับอะไรบ้าง?
โมดูล Notification รองรับการส่งในแอป (ค่าเริ่มต้น) และสามารถเปิดใช้งานอีเมลหรือ LINE Notify ได้จากการตั้งค่าผู้ใช้/ระบบ หากเปิดใช้งาน ระบบจะบันทึกช่องทางที่ส่งและข้อผิดพลาดไว้ในฐานข้อมูล.【F:backend/app/models/notification.py†L1-L48】【F:backend/app/core/config.py†L29-L47】

### Q7: ทำไมการอัปโหลดใบเสร็จถูกปฏิเสธ?
ตรวจสอบว่าได้เช็กอินงานก่อน (ต้องมีสถานะ `checkin_datetime`) และไฟล์ต้องอยู่ในชนิด/ขนาดที่อนุญาต (`jpg`, `png`, `pdf` ภายใต้ `MAX_FILE_SIZE`). หากไม่ตรงตามนี้ API จะตอบกลับ `400 Bad Request` พร้อมข้อความแจ้ง.【F:backend/app/api/api_v1/endpoints/job_runs.py†L145-L197】【F:backend/app/core/config.py†L29-L41】
