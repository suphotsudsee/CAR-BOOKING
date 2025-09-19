# คู่มือการใช้งานระบบจองรถสำหรับผู้ใช้ทุกระดับ

## 1. ทำความเข้าใจระบบโดยรวม
- ระบบรองรับบทบาทหลัก 5 กลุ่ม ได้แก่ ผู้ขอใช้รถ (Requester), ผู้จัดการ (Manager), ผู้ดูแลยานพาหนะ (Fleet Admin), คนขับ (Driver) และผู้ตรวจสอบ (Auditor) โดยแดชบอร์ดจะแสดงข้อมูลและคำแนะนำเฉพาะสำหรับบทบาทที่ล็อกอินอยู่ทุกครั้ง.【F:frontend/src/context/AuthContext.tsx†L16-L84】【F:frontend/src/app/dashboard/page.tsx†L21-L207】
- ค่ากำหนดระดับองค์กร เช่น เวลาทำการ, จำนวนคำขอที่รออนุมัติสูงสุด, ระยะเวลายกเลิกอัตโนมัติ และการบังคับอนุมัติ ล้วนตั้งค่าได้จากโมดูล System Configuration ซึ่งส่งผลกับผู้ใช้ทุกบทบาท.【F:backend/app/models/system.py†L14-L58】

## 2. เริ่มต้นใช้งาน (ทุกบทบาท)
1. **ลงทะเบียนบัญชีใหม่:** กรอกข้อมูลส่วนตัว เลือกบทบาทเบื้องต้น (พนักงาน, คนขับ, ผู้ดูแล) ยืนยันว่ารหัสผ่านตรงตามนโยบายความปลอดภัย และยอมรับเงื่อนไขการใช้ระบบ จากนั้นระบบจะสร้างบัญชีและส่งอีเมลยืนยันให้เปิดใช้งาน.【F:frontend/src/app/register/page.tsx†L10-L200】
2. **เข้าสู่ระบบ:** ใช้ชื่อผู้ใช้หรืออีเมลและรหัสผ่าน หากต้องการให้ระบบจำการเข้าสู่ระบบสามารถเปิดตัวเลือก “จดจำการเข้าสู่ระบบ” และรีไดเรกต์สู่แดชบอร์ดอัตโนมัติหลังยืนยันตัวตนสำเร็จ.【F:frontend/src/app/login/page.tsx†L13-L149】
3. **โหลดโปรไฟล์และเซสชัน:** หลังล็อกอิน AuthContext จะดึงข้อมูลผู้ใช้ สิทธิ์ และโทเคน เพื่อเลือกแดชบอร์ดที่เหมาะสม พร้อมจัดการการต่ออายุโทเคนให้อัตโนมัติหากเลือกจดจำเซสชัน.【F:frontend/src/context/AuthContext.tsx†L37-L200】
4. **สำรวจแดชบอร์ด:** หน้า `/dashboard` แสดงการ์ดสถิติหลัก การแจ้งเตือนล่าสุด และเนื้อหาเฉพาะบทบาท พร้อมปุ่มลัดไปยังฟีเจอร์สำคัญของแต่ละกลุ่มผู้ใช้.【F:frontend/src/app/dashboard/page.tsx†L134-L286】

## 3. การแจ้งเตือนและความปลอดภัย
- วิดเจ็ตการแจ้งเตือนในแดชบอร์ดจะแสดงรายการล่าสุดและจำนวนแจ้งเตือนที่ยังไม่ได้อ่าน พร้อมปุ่มรีเฟรชเพื่อดึงข้อมูลแบบเรียลไทม์.【F:frontend/src/app/dashboard/page.tsx†L74-L131】
- ระบบบันทึกการแจ้งเตือนในฐานข้อมูล พร้อมรองรับหลายช่องทาง (ในแอป, อีเมล, LINE) และให้ผู้ใช้กำหนดค่าความชอบการรับแจ้งเตือนได้ภายหลัง.【F:backend/app/models/notification.py†L16-L122】
- ผู้ใช้บทบาทสูง (เช่น ผู้ดูแลระบบ) ควรเปิดใช้งานการยืนยันตัวตนสองชั้นตามที่ระบุในหน้าลงทะเบียน และปฏิบัติตามนโยบายรหัสผ่านเพื่อรักษาความปลอดภัยของระบบ.【F:frontend/src/app/register/page.tsx†L181-L188】

## 4. ขั้นตอนการทำงานตามบทบาท
### 4.1 ผู้ขอใช้รถ (Requester)
1. เข้าสู่แดชบอร์ดเพื่อดูสถิติคำขอรอดำเนินการ ประวัติอนุมัติ และชั่วโมงการใช้งานล่าสุด พร้อมปุ่มลัดสำหรับสร้างคำขอใหม่หรือดูปฏิทินการใช้รถ.【F:frontend/src/components/dashboard/RequesterDashboard.tsx†L60-L126】
2. กด “สร้างคำขอจองรถ” เพื่อเปิดฟอร์ม กรอกรายละเอียดการเดินทาง ระบบจะป้องกันไม่ให้เลือกผู้ร้องคนอื่นเว้นแต่มีสิทธิ์ผู้จัดการหรือสูงกว่า และจะบันทึกคำขอในสถานะ `REQUESTED`.【F:frontend/src/components/dashboard/RequesterDashboard.tsx†L97-L110】【F:backend/app/api/api_v1/endpoints/bookings.py†L86-L116】
3. ติดตามผลอนุมัติผ่านตาราง “ประวัติการจองล่าสุด” หรือเรียกดูคำขอทั้งหมดผ่าน API `/api/v1/bookings/me` ที่รองรับการค้นหาและกรองตามสถานะ/ช่วงเวลา.【F:frontend/src/components/dashboard/RequesterDashboard.tsx†L128-L153】【F:backend/app/api/api_v1/endpoints/bookings.py†L155-L184】
4. หากต้องการแก้ไขหรือยกเลิกคำขอก่อนอนุมัติ สามารถส่งคำสั่งอัปเดตได้ ระบบจะตรวจสอบสิทธิ์ผู้ร้องและสถานะคำขอเพื่อป้องกันการแก้ไขหลังอนุมัติ.【F:backend/app/api/api_v1/endpoints/bookings.py†L202-L216】
5. สร้างคำขอล่วงหน้าอย่างน้อย 4 ชั่วโมงตามการตั้งค่า `booking_lead_time_hours` เพื่อลดโอกาสถูกปฏิเสธอัตโนมัติ และหลีกเลี่ยงการมีคำขอค้างเกินโควตาต่อผู้ใช้.【F:backend/app/models/system.py†L24-L58】

### 4.2 ผู้จัดการ (Manager)
1. แดชบอร์ดจะแสดงจำนวนคำขอรออนุมัติ เวลาตอบสนองเฉลี่ย และคำขอที่รอข้อมูลเพิ่มเติม เพื่อช่วยควบคุม SLA ของทีม.【F:frontend/src/components/dashboard/ManagerDashboard.tsx†L76-L107】
2. ใช้ส่วน “คิวคำขอที่ต้องอนุมัติ” เพื่อตรวจสอบรายละเอียดแบบไทม์ไลน์ หรือคลิกปุ่ม “ตรวจสอบคำขอทั้งหมด” เพื่อเข้าสู่หน้ารวมรายการอนุมัติ.【F:frontend/src/components/dashboard/ManagerDashboard.tsx†L109-L197】
3. เรียก API `/api/v1/bookings` เพื่อค้นหาและกรองคำขอ (สถานะ ผู้ร้อง แผนก ช่วงเวลา) จากนั้นอนุมัติ/ปฏิเสธด้วย `/api/v1/bookings/{id}/approve|reject` พร้อมระบุเหตุผล ระบบจะสร้างการแจ้งเตือนให้ผู้ร้องโดยอัตโนมัติ.【F:frontend/src/components/dashboard/ManagerDashboard.tsx†L168-L197】【F:backend/app/api/api_v1/endpoints/bookings.py†L118-L343】
4. หากต้องการขอข้อมูลเพิ่มหรือส่งต่อให้ผู้ร้องแก้ไข ใช้เอ็นด์พอยต์สถานะ `/api/v1/bookings/{id}/status` เพื่อเปลี่ยนเป็นสถานะที่เหมาะสมก่อนดำเนินการต่อ.【F:backend/app/api/api_v1/endpoints/bookings.py†L257-L301】
5. ตั้งค่าผู้อนุมัติแทนเมื่อไม่อยู่ โดยระบบบันทึกในตาราง `approval_delegations` และใช้ในการตรวจสอบสิทธิ์ผู้แทนในอนาคต.【F:frontend/src/components/dashboard/ManagerDashboard.tsx†L169-L197】【F:backend/app/models/approval.py†L63-L91】

### 4.3 ผู้ดูแลยานพาหนะ (Fleet Admin)
1. ตรวจสอบการ์ดสถิติสำหรับอัตราการใช้งาน ความพร้อมของรถ และค่าใช้จ่าย ก่อนลงมือจัดการทรัพยากรผ่านส่วน “รายการยานพาหนะและทรัพยากร”.【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L125-L147】
2. ใช้ API `/api/v1/vehicles` เพื่อค้นหา กรอง และอัปเดตข้อมูลรถ รวมถึงสร้างรถคันใหม่หรือแนบเอกสารสำคัญของรถผ่านเอ็นด์พอยต์ที่เกี่ยวข้อง.【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L174-L204】【F:backend/app/api/api_v1/endpoints/vehicles.py†L50-L220】
3. วางแผนบำรุงรักษาผ่านส่วน “กำหนดการบำรุงรักษา” และผูกเข้าปฏิทินได้ทันที ช่วยลดการชนกับคำขอเดินทางในอนาคต.【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L149-L171】
4. ติดตามการแจ้งเตือนเอกสารหรือปัญหา IoT เพื่อจัดการเชิงรุก และใช้ API `/api/v1/vehicles/document-expiry` สำหรับแจ้งเตือนเอกสารใกล้หมดอายุ.【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L206-L220】【F:backend/app/api/api_v1/endpoints/vehicles.py†L76-L96】
5. อัปเดตสถานะรถหรือมอบหมายคนขับทันทีเมื่อมีการเปลี่ยนแปลง เพื่อให้ข้อมูลตรงกับคำขอในระบบและลดความเสี่ยงการจัดรถผิดคิว.【F:backend/app/api/api_v1/endpoints/vehicles.py†L128-L170】【F:backend/app/api/api_v1/endpoints/drivers.py†L40-L200】

### 4.4 คนขับ (Driver)
1. แดชบอร์ดแสดงงานวันนี้ งานที่เสร็จสิ้น และเวลาว่าง พร้อมปุ่มเช็กอิน/เช็กเอาต์ และการ์ดติดตามตำแหน่งเพื่อให้ข้อมูลการเดินทางครบถ้วน.【F:frontend/src/components/dashboard/DriverDashboard.tsx†L60-L219】
2. ก่อนออกเดินทางให้กดเช็กอิน ระบบจะบันทึกเวลา ตำแหน่ง และภาพยืนยัน พร้อมเริ่มติดตาม GPS อัตโนมัติ หากไม่มีสัญญาณให้เริ่ม/หยุดการติดตามใหม่ตามคำแนะนำที่ปรากฏ.【F:frontend/src/components/dashboard/DriverDashboard.tsx†L101-L180】
3. หลังจบงานให้กดเช็กเอาต์เพื่อหยุดการติดตามและบันทึกตำแหน่งสุดท้าย ระบบจะเก็บประวัติการเช็กอิน/เช็กเอาต์ไว้ไม่เกิน 6 รายการล่าสุดเพื่อให้ทบทวนง่าย.【F:frontend/src/components/dashboard/DriverDashboard.tsx†L132-L169】
4. หากมีค่าใช้จ่าย ให้ถ่ายภาพใบเสร็จและอัปโหลดผ่านเมนูค่าใช้จ่าย ระบบจะตรวจสอบขนาดไฟล์ นามสกุล และแนบเข้ากับงานที่เกี่ยวข้องให้อัตโนมัติ.【F:backend/app/api/api_v1/endpoints/job_runs.py†L145-L197】
5. API `job-runs` ตรวจสอบสิทธิ์คนขับและสถานะงานก่อนอนุญาตให้เช็กอิน/เช็กเอาต์ เพื่อความถูกต้องของข้อมูลภาคสนาม.【F:backend/app/api/api_v1/endpoints/job_runs.py†L200-L258】

## 5. เคล็ดลับการใช้งานร่วมกัน
- ตรวจสอบการแจ้งเตือนอย่างสม่ำเสมอเพื่อทราบผลอนุมัติ การเปลี่ยนสถานะ หรือคำขอข้อมูลเพิ่มเติม โดยแจ้งเตือนจะซิงก์ทั้งแดชบอร์ดและฐานข้อมูลกลาง.【F:frontend/src/app/dashboard/page.tsx†L74-L131】【F:backend/app/models/notification.py†L24-L75】
- รักษาข้อมูลให้เป็นปัจจุบัน: ผู้ขอใช้รถควรปิดคำขอที่ไม่ใช้, ผู้จัดการควรเคลียร์คิวอนุมัติทุกวัน, ผู้ดูแลยานพาหนะควรอัปเดตสถานะรถหลังซ่อม, คนขับควรเช็กอิน/เอาต์ตรงเวลา เพื่อให้สถิติเชิงวิเคราะห์ถูกต้อง.【F:frontend/src/components/dashboard/RequesterDashboard.tsx†L128-L153】【F:frontend/src/components/dashboard/ManagerDashboard.tsx†L76-L160】【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L125-L204】【F:frontend/src/components/dashboard/DriverDashboard.tsx†L101-L219】
- ใช้รายงานและปฏิทินเพื่อวางแผนระยะยาว โดยแดชบอร์ดแต่ละบทบาทมีปุ่มลัดไปยังหน้าเชิงลึก เช่น รายงานการใช้ทีม รายงานยานพาหนะ หรือปฏิทินงานเพื่อปรับตารางล่วงหน้า.【F:frontend/src/app/dashboard/page.tsx†L241-L286】【F:frontend/src/components/dashboard/ManagerDashboard.tsx†L168-L197】【F:frontend/src/components/dashboard/FleetAdminDashboard.tsx†L174-L204】【F:frontend/src/components/dashboard/RequesterDashboard.tsx†L111-L125】

## 6. แหล่งข้อมูลเพิ่มเติม
- คู่มือย่อยสำหรับแต่ละบทบาท (Requester, Manager, Fleet Admin, Driver) อยู่ในโฟลเดอร์ `docs/user/` สามารถอ้างอิงรายละเอียดเชิงลึกเพิ่มเติมได้
- ระบบ API แบบเต็มสามารถตรวจสอบได้จากไฟล์ OpenAPI หรือ Swagger UI ภายใต้ `docs/system/api/`
