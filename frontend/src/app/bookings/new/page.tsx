import { NewBookingForm } from '@/components/bookings/NewBookingForm';

export default function NewBookingPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-wide text-primary-500">Booking Request</p>
        <h1 className="text-4xl font-bold text-gray-900">สร้างคำขอจองรถใหม่</h1>
        <p className="max-w-3xl text-sm text-gray-600">
          ใช้แบบฟอร์มหลายขั้นตอนเพื่อให้รายละเอียดครบถ้วน ตั้งแต่ข้อมูลผู้โดยสาร กำหนดการเดินทาง ไปจนถึงความต้องการพิเศษ ระบบจะช่วยตรวจสอบความพร้อมของยานพาหนะและแจ้งเตือนความขัดแย้งให้อัตโนมัติ
        </p>
      </div>
      <NewBookingForm />
    </div>
  );
}
