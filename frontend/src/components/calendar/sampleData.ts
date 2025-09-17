import { addHours, startOfDay } from 'date-fns';

import { vehicleOptions } from '@/components/bookings/sampleData';

export type CalendarStatus =
  | 'planned'
  | 'pending'
  | 'confirmed'
  | 'inProgress'
  | 'completed'
  | 'cancelled';

export interface CalendarVehicleResource {
  id: string;
  name: string;
  type: string;
  capacity: number;
  status: 'available' | 'maintenance' | 'assigned';
  features: string[];
  location: string;
}

export interface CalendarDriverResource {
  id: string;
  name: string;
  phone: string;
  email: string;
  skills: string[];
  licenseClasses: string[];
  availability: 'available' | 'onDuty' | 'leave';
  preferredVehicleTypes: string[];
}

export interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  requester: string;
  department: string;
  vehicleId: string;
  driverId: string;
  status: CalendarStatus;
  location: string;
  passengers: number;
  notes?: string;
  allowSharing?: boolean;
  color?: string;
}

export const calendarVehicles: CalendarVehicleResource[] = vehicleOptions.map((vehicle) => ({
  ...vehicle,
}));

export const calendarDrivers: CalendarDriverResource[] = [
  {
    id: 'DRV-001',
    name: 'พรเทพ ตั้งมั่น',
    phone: '081-234-5678',
    email: 'pornthep@example.com',
    skills: ['ภาษาอังกฤษ', 'งานพิธีการ', 'VIP Protocol'],
    licenseClasses: ['ประเภท 2', 'ประเภท 3'],
    availability: 'available',
    preferredVehicleTypes: ['Sedan', 'SUV'],
  },
  {
    id: 'DRV-002',
    name: 'จิราพร ศรีสุข',
    phone: '089-876-5432',
    email: 'jiraporn@example.com',
    skills: ['ขับรถระยะไกล', 'ความปลอดภัยขั้นสูง'],
    licenseClasses: ['ประเภท 2'],
    availability: 'onDuty',
    preferredVehicleTypes: ['Van', 'Pickup'],
  },
  {
    id: 'DRV-003',
    name: 'กิตติภพ พานทอง',
    phone: '080-555-1923',
    email: 'kittiphop@example.com',
    skills: ['ภาษาจีน', 'งานบริการลูกค้า'],
    licenseClasses: ['ประเภท 2', 'ประเภท 4'],
    availability: 'available',
    preferredVehicleTypes: ['SUV', 'Van'],
  },
  {
    id: 'DRV-004',
    name: 'สิริขวัญ ชูเกียรติ',
    phone: '086-333-7788',
    email: 'sirikhwan@example.com',
    skills: ['การแพทย์ฉุกเฉิน', 'รถพิเศษ'],
    licenseClasses: ['ประเภท 2'],
    availability: 'available',
    preferredVehicleTypes: ['Van', 'Pickup'],
  },
  {
    id: 'DRV-005',
    name: 'อนุชา เหล่ากาญจน์',
    phone: '082-147-2589',
    email: 'anucha@example.com',
    skills: ['งานราชการ', 'ขับขบวน'],
    licenseClasses: ['ประเภท 2', 'ประเภท 3'],
    availability: 'leave',
    preferredVehicleTypes: ['Sedan', 'Van'],
  },
];

const baseDay = startOfDay(new Date());

function event(id: string, startOffsetHours: number, durationHours: number, overrides?: Partial<CalendarEvent>): CalendarEvent {
  const start = addHours(baseDay, startOffsetHours);
  const end = addHours(start, durationHours);
  return {
    id,
    title: 'งานขนส่งภารกิจ',
    requester: 'ระบบอัตโนมัติ',
    department: 'ส่วนกลาง',
    vehicleId: calendarVehicles[0]?.id ?? 'VHC-001',
    driverId: calendarDrivers[0]?.id ?? 'DRV-001',
    status: 'confirmed',
    location: 'สำนักงานใหญ่',
    passengers: 3,
    start,
    end,
    ...overrides,
  };
}

export const initialCalendarEvents: CalendarEvent[] = [
  event('CAL-001', 8, 3, {
    title: 'รับผู้บริหารจากสนามบิน',
    requester: 'ศศิประภา จันทร์ทอง',
    department: 'ฝ่ายขาย',
    vehicleId: 'VHC-001',
    driverId: 'DRV-001',
    status: 'confirmed',
    location: 'ท่าอากาศยานสุวรรณภูมิ',
    notes: 'เตรียมน้ำดื่มและผ้าเย็น',
  }),
  event('CAL-002', 13, 4, {
    title: 'ประชุมภาคสนามชลบุรี',
    requester: 'วิศวะ พัฒนกิจ',
    department: 'วิศวกรรม',
    vehicleId: 'VHC-003',
    driverId: 'DRV-003',
    status: 'pending',
    location: 'นิคมอุตสาหกรรมอมตะซิตี้',
    passengers: 6,
  }),
  event('CAL-003', 9, 2, {
    title: 'ขนส่งอุปกรณ์โครงการ',
    requester: 'พิมพ์ชนก ตั้งตรง',
    department: 'คลังสินค้า',
    vehicleId: 'VHC-005',
    driverId: 'DRV-002',
    status: 'inProgress',
    location: 'คลังสินค้ารังสิต',
    passengers: 2,
  }),
  event('CAL-004', 15, 3, {
    title: 'ดูงานศูนย์ฝึกอบรม',
    requester: 'จิรายุทธ ทองดี',
    department: 'พัฒนาบุคลากร',
    vehicleId: 'VHC-003',
    driverId: 'DRV-004',
    status: 'planned',
    location: 'ศูนย์ฝึกอบรมบางนา',
    passengers: 8,
  }),
  event('CAL-005', 18, 2, {
    title: 'ส่งทีมงานดึก',
    requester: 'นภัสสร อินทร',
    department: 'ฝ่ายผลิต',
    vehicleId: 'VHC-002',
    driverId: 'DRV-002',
    status: 'confirmed',
    location: 'โรงงานผลิตบางปะอิน',
    passengers: 10,
  }),
  event('CAL-006', -2, 4, {
    title: 'ตรวจรับรถใหม่',
    requester: 'ฝ่ายพัสดุ',
    department: 'จัดซื้อ',
    vehicleId: 'VHC-004',
    driverId: 'DRV-005',
    status: 'cancelled',
    location: 'ศูนย์บริการยานพาหนะ',
    passengers: 2,
  }),
];
