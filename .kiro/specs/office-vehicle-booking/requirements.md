# Requirements Document - Office Vehicle Booking System

## Introduction

ระบบจองรถสำนักงาน (Office Vehicle Booking System) เป็นระบบที่พัฒนาขึ้นเพื่อให้พนักงานสามารถขอใช้รถสำนักงานได้อย่างมีประสิทธิภาพ ป้องกันการจองที่ชนกัน และมีขั้นตอนการอนุมัติที่ชัดเจน รวมถึงการจัดการรถ คนขับ ตารางงาน และการบำรุงรักษาในที่เดียว พร้อมทั้งสร้างหลักฐานการใช้งานและรายงานสำหรับผู้บริหาร

## Requirements

### Requirement 1: Vehicle Management

**User Story:** ในฐานะ Fleet Admin ฉันต้องการจัดการข้อมูลรถยนต์ในระบบ เพื่อให้สามารถติดตามสถานะและเอกสารที่เกี่ยวข้องได้

#### Acceptance Criteria

1. WHEN Fleet Admin เพิ่มรถใหม่ THEN ระบบ SHALL บันทึกข้อมูลทะเบียน ประเภท ความจุที่นั่ง ยี่ห้อ รุ่น และสถานะ
2. WHEN Fleet Admin กรอกวันหมดอายุ พ.ร.บ./ประกัน/ภาษี THEN ระบบ SHALL แจ้งเตือนล่วงหน้า 30 วันก่อนหมดอายุ
3. WHEN รถมีสถานะ "MAINTENANCE" THEN ระบบ SHALL ไม่แสดงรถคันนั้นในตัวเลือกการจอง
4. WHEN Fleet Admin แก้ไขข้อมูลรถ THEN ระบบ SHALL บันทึก audit log พร้อมผู้แก้ไขและเวลา

### Requirement 2: Driver Management

**User Story:** ในฐานะ Fleet Admin ฉันต้องการจัดการข้อมูลคนขับ เพื่อให้สามารถจัดสรรงานได้อย่างเหมาะสม

#### Acceptance Criteria

1. WHEN Fleet Admin เพิ่มคนขับใหม่ THEN ระบบ SHALL บันทึกรหัสพนักงาน ชื่อ เบอร์โทร เลขใบขับขี่ และวันหมดอายุ
2. WHEN ใบขับขี่ใกล้หมดอายุ 60 วัน THEN ระบบ SHALL แจ้งเตือน Fleet Admin และคนขับ
3. WHEN คนขับมีสถานะ "INACTIVE" THEN ระบบ SHALL ไม่แสดงในตัวเลือกการจัดสรรงาน
4. WHEN Fleet Admin ตั้งค่าความพร้อมใช้งานคนขับ THEN ระบบ SHALL บันทึกช่วงเวลาที่พร้อมทำงาน

### Requirement 3: Booking Request

**User Story:** ในฐานะ Requester ฉันต้องการจองรถสำนักงาน เพื่อใช้ในการเดินทางไปปฏิบัติงาน

#### Acceptance Criteria

1. WHEN Requester กรอกฟอร์มจอง THEN ระบบ SHALL เก็บข้อมูลวันที่/เวลาไป-กลับ จุดรับ-ส่ง วัตถุประสงค์ จำนวนผู้โดยสาร และประเภทรถที่ต้องการ
2. WHEN Requester เลือกช่วงเวลา THEN ระบบ SHALL ตรวจสอบการชนกันและแสดงรถที่ว่าง
3. WHEN มีการจองที่ชนกัน THEN ระบบ SHALL แสดงข้อความเตือนและแนะนำช่วงเวลาอื่น
4. WHEN Requester ส่งคำขอ THEN ระบบ SHALL เปลี่ยนสถานะเป็น "REQUESTED" และส่งแจ้งเตือนให้ Manager

### Requirement 4: Approval Workflow

**User Story:** ในฐานะ Manager ฉันต้องการอนุมัติคำขอใช้รถของทีม เพื่อควบคุมการใช้ทรัพยากร

#### Acceptance Criteria

1. WHEN Manager เข้าดูคำขออนุมัติ THEN ระบบ SHALL แสดงรายละเอียดการจอง วัตถุประสงค์ และข้อมูลผู้ขอ
2. WHEN Manager อนุมัติคำขอ THEN ระบบ SHALL เปลี่ยนสถานะเป็น "APPROVED" และส่งแจ้งเตือนให้ Fleet Admin
3. WHEN Manager ปฏิเสธคำขอ THEN ระบบ SHALL บันทึกเหตุผลและแจ้งเตือนผู้ขอ
4. WHEN คำขอได้รับการอนุมัติ THEN ระบบ SHALL ป้องกันไม่ให้ Requester แก้ไขหรือยกเลิกเอง

### Requirement 5: Vehicle and Driver Assignment

**User Story:** ในฐานะ Fleet Admin ฉันต้องการจัดสรรรถและคนขับให้กับคำขอที่อนุมัติแล้ว เพื่อให้การดำเนินงานเป็นไปอย่างราบรื่น

#### Acceptance Criteria

1. WHEN Fleet Admin เข้าดูคำขอที่อนุมัติแล้ว THEN ระบบ SHALL แสดงรายการรถและคนขับที่ว่างในช่วงเวลานั้น
2. WHEN Fleet Admin จัดสรรรถและคนขับ THEN ระบบ SHALL ตรวจสอบความขัดแย้งอีกครั้งก่อนบันทึก
3. WHEN การจัดสรรเสร็จสิ้น THEN ระบบ SHALL ส่งแจ้งเตือนให้คนขับและสร้างใบงาน
4. WHEN Fleet Admin ต้องการเปลี่ยนการจัดสรร THEN ระบบ SHALL อนุญาตให้แก้ไขก่อนวันเดินทาง 24 ชั่วโมง

### Requirement 6: Job Execution and Check-in/Check-out

**User Story:** ในฐานะ Driver ฉันต้องการเช็คอิน/เช็คเอาท์งานที่ได้รับมอบหมาย เพื่อบันทึกการใช้งานรถอย่างถูกต้อง

#### Acceptance Criteria

1. WHEN Driver เช็คอินงาน THEN ระบบ SHALL บันทึกเวลาจริง เลขไมล์เริ่มต้น และรูปภาพสภาพรถก่อนใช้งาน
2. WHEN Driver เช็คเอาท์งาน THEN ระบบ SHALL บันทึกเวลาจริง เลขไมล์สิ้นสุด รูปภาพสภาพรถหลังใช้งาน และค่าใช้จ่าย
3. WHEN มีเหตุการณ์ผิดปกติ THEN ระบบ SHALL อนุญาตให้ Driver บันทึกรายละเอียดเหตุการณ์
4. WHEN งานเสร็จสิ้น THEN ระบบ SHALL เปลี่ยนสถานะเป็น "DONE" และคำนวณระยะทางรวม

### Requirement 7: Calendar and Resource View

**User Story:** ในฐานะ Fleet Admin ฉันต้องการดูปฏิทินการใช้งานรถและคนขับ เพื่อวางแผนการจัดสรรได้อย่างมีประสิทธิภาพ

#### Acceptance Criteria

1. WHEN Fleet Admin เข้าดูปฏิทิน THEN ระบบ SHALL แสดงตารางการใช้งานแยกตามรถและคนขับ
2. WHEN มีการจองใหม่ THEN ระบบ SHALL อัปเดตปฏิทินแบบ real-time
3. WHEN Fleet Admin คลิกที่งานในปฏิทิน THEN ระบบ SHALL แสดงรายละเอียดงานและอนุญาตให้แก้ไข
4. WHEN มีงานที่ทับซ้อน THEN ระบบ SHALL แสดงสีแดงเตือนและรายละเอียดความขัดแย้ง

### Requirement 8: Reporting and Analytics

**User Story:** ในฐานะผู้บริหาร ฉันต้องการดูรายงานการใช้งานรถ เพื่อวิเคราะห์ประสิทธิภาพและวางแผนการจัดซื้อ

#### Acceptance Criteria

1. WHEN ผู้บริหารขอรายงานรายเดือน THEN ระบบ SHALL แสดงอัตราการใช้งานรถแต่ละคัน ระยะทางรวม และค่าน้ำมัน
2. WHEN ผู้บริหารต้องการ export ข้อมูล THEN ระบบ SHALL สร้างไฟล์ CSV หรือ PDF ตามที่เลือก
3. WHEN มีการขอรายงานตามหน่วยงาน THEN ระบบ SHALL แยกข้อมูลตามแผนกที่เลือก
4. WHEN ผู้บริหารดูแดชบอร์ด THEN ระบบ SHALL แสดง KPI สำคัญ เช่น อัตราการจองชน เวลาเฉลี่ยการอนุมัติ และ utilization rate

### Requirement 9: Notification System

**User Story:** ในฐานะผู้ใช้ระบบ ฉันต้องการได้รับแจ้งเตือนเมื่อมีการเปลี่ยนแปลงสถานะ เพื่อติดตามงานได้ทันท่วงที

#### Acceptance Criteria

1. WHEN มีคำขอใหม่ THEN ระบบ SHALL ส่งแจ้งเตือนให้ Manager ผ่านอีเมล
2. WHEN คำขอได้รับอนุมัติ/ปฏิเสธ THEN ระบบ SHALL แจ้งเตือน Requester และ Fleet Admin
3. WHEN มีการจัดสรรรถและคนขับ THEN ระบบ SHALL แจ้งเตือน Driver ที่ได้รับมอบหมาย
4. WHEN เอกสารรถใกล้หมดอายุ THEN ระบบ SHALL แจ้งเตือน Fleet Admin ล่วงหน้า 30 วัน

### Requirement 10: Security and Access Control

**User Story:** ในฐานะ System Administrator ฉันต้องการควบคุมสิทธิ์การเข้าถึงระบบ เพื่อรักษาความปลอดภัยของข้อมูล

#### Acceptance Criteria

1. WHEN ผู้ใช้เข้าสู่ระบบ THEN ระบบ SHALL ตรวจสอบ username/password และ role-based permissions
2. WHEN Fleet Admin หรือ Manager เข้าสู่ระบบ THEN ระบบ SHALL ต้องการ 2FA authentication
3. WHEN มีการเข้าถึงข้อมูลสำคัญ THEN ระบบ SHALL บันทึก audit log พร้อมรายละเอียดผู้ใช้และเวลา
4. WHEN ผู้ใช้พยายามเข้าถึงข้อมูลที่ไม่มีสิทธิ์ THEN ระบบ SHALL ปฏิเสธและบันทึก security event

### Requirement 11: Mobile Support

**User Story:** ในฐานะ Driver ฉันต้องการใช้งานระบบผ่านมือถือ เพื่อเช็คอิน/เช็คเอาท์และถ่ายรูปได้สะดวก

#### Acceptance Criteria

1. WHEN Driver เข้าใช้งานผ่านมือถือ THEN ระบบ SHALL แสดงหน้าจอที่เหมาะสมกับขนาดหน้าจอ
2. WHEN Driver ถ่ายรูปสภาพรถ THEN ระบบ SHALL บันทึกรูปพร้อม GPS location และ timestamp
3. WHEN Driver ไม่มีสัญญาณอินเทอร์เน็ต THEN ระบบ SHALL เก็บข้อมูลไว้ใน cache และ sync เมื่อมีสัญญาณ
4. WHEN Driver ดูงานที่ได้รับมอบหมาย THEN ระบบ SHALL แสดงรายละเอียดงาน แผนที่ และข้อมูลติดต่อผู้โดยสาร

### Requirement 12: Data Backup and Recovery

**User Story:** ในฐานะ System Administrator ฉันต้องการระบบสำรองข้อมูลที่เชื่อถือได้ เพื่อป้องกันการสูญหายของข้อมูล

#### Acceptance Criteria

1. WHEN ระบบทำงานตามปกติ THEN ระบบ SHALL สำรองข้อมูลอัตโนมัติทุกวันเวลา 02:00 น.
2. WHEN เกิดความผิดพลาดของระบบ THEN ระบบ SHALL สามารถกู้คืนข้อมูลจาก backup ล่าสุดได้ภายใน 4 ชั่วโมง
3. WHEN มีการเปลี่ยนแปลงข้อมูลสำคัญ THEN ระบบ SHALL เก็บ incremental backup ทุก 6 ชั่วโมง
4. WHEN System Administrator ต้องการทดสอบการกู้คืน THEN ระบบ SHALL มีกระบวนการทดสอบ backup integrity รายเดือน