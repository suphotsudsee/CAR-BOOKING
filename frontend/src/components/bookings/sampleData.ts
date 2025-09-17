export interface VehicleOption {
  id: string;
  name: string;
  type: string;
  capacity: number;
  features: string[];
  status: 'available' | 'maintenance' | 'assigned';
  location: string;
}

export interface BookingRecord {
  id: string;
  requester: string;
  department: string;
  purpose: string;
  origin: string;
  destination: string;
  start: string;
  end: string;
  status: 'Draft' | 'Pending' | 'Approved' | 'Rejected' | 'InProgress' | 'Completed' | 'Cancelled';
  passengers: number;
  vehicleId?: string;
  driver?: string;
  notes?: string;
  approvals?: Array<{
    id: string;
    approver: string;
    role: string;
    status: 'Pending' | 'Approved' | 'Rejected';
    updatedAt: string;
    comment?: string;
  }>;
  history?: Array<{
    id: string;
    label: string;
    description: string;
    timestamp: string;
    state: 'complete' | 'current' | 'upcoming';
  }>;
}

export const vehicleOptions: VehicleOption[] = [
  {
    id: 'VHC-001',
    name: 'Toyota Camry',
    type: 'Sedan',
    capacity: 4,
    features: ['Wi-Fi', 'Dash Cam', 'Navigation'],
    status: 'available',
    location: 'สำนักงานใหญ่',
  },
  {
    id: 'VHC-002',
    name: 'Toyota Commuter',
    type: 'Van',
    capacity: 12,
    features: ['ทีวี', 'USB Charger', 'Cooler'],
    status: 'assigned',
    location: 'อาคารจอดรถฝั่งตะวันออก',
  },
  {
    id: 'VHC-003',
    name: 'Hyundai H1',
    type: 'Van',
    capacity: 7,
    features: ['Leather Seat', 'Dual AC', 'Navigation'],
    status: 'available',
    location: 'ศูนย์บริการยานพาหนะ',
  },
  {
    id: 'VHC-004',
    name: 'Mitsubishi Pajero Sport',
    type: 'SUV',
    capacity: 5,
    features: ['4WD', 'Roof Rack', 'CarPlay'],
    status: 'maintenance',
    location: 'ศูนย์บำรุงรักษา',
  },
  {
    id: 'VHC-005',
    name: 'Nissan Navara',
    type: 'Pickup',
    capacity: 5,
    features: ['4WD', 'Cargo Cover', 'Dash Cam'],
    status: 'available',
    location: 'คลังสินค้าฝั่งเหนือ',
  },
];

export const existingScheduleConflicts: Array<{
  id: string;
  vehicleId: string;
  start: string;
  end: string;
  summary: string;
}> = [
  {
    id: 'BK-2024-1001',
    vehicleId: 'VHC-001',
    start: '2024-02-18T08:00:00+07:00',
    end: '2024-02-18T12:30:00+07:00',
    summary: 'รับผู้บริหารจากสนามบินสุวรรณภูมิ',
  },
  {
    id: 'BK-2024-1002',
    vehicleId: 'VHC-003',
    start: '2024-02-18T13:00:00+07:00',
    end: '2024-02-18T17:30:00+07:00',
    summary: 'ประชุมภาคสนามที่จังหวัดชลบุรี',
  },
  {
    id: 'BK-2024-1003',
    vehicleId: 'VHC-005',
    start: '2024-02-19T09:30:00+07:00',
    end: '2024-02-19T18:00:00+07:00',
    summary: 'ขนส่งอุปกรณ์โครงการ',
  },
];

export const popularLocations = [
  {
    id: 'LOC-001',
    name: 'สำนักงานใหญ่',
    address: 'ถนนเพลินจิต เขตปทุมวัน กรุงเทพฯ',
    latitude: 13.743894,
    longitude: 100.549111,
  },
  {
    id: 'LOC-002',
    name: 'ศูนย์ฝึกอบรมบางนา',
    address: 'ถนนบางนา-ตราด กม. 12 สมุทรปราการ',
    latitude: 13.631353,
    longitude: 100.735188,
  },
  {
    id: 'LOC-003',
    name: 'คลังสินค้ารังสิต',
    address: 'ถนนพหลโยธิน คลองหนึ่ง ปทุมธานี',
    latitude: 14.063732,
    longitude: 100.616776,
  },
  {
    id: 'LOC-004',
    name: 'นิคมอุตสาหกรรมอมตะซิตี้',
    address: 'ถนนบางนา-ตราด กม. 57 ชลบุรี',
    latitude: 13.455612,
    longitude: 101.005843,
  },
  {
    id: 'LOC-005',
    name: 'ท่าอากาศยานสุวรรณภูมิ',
    address: 'ถนนบางนา-ตราด สมุทรปราการ',
    latitude: 13.690067,
    longitude: 100.75005,
  },
];

export const mockBookings: BookingRecord[] = [
  {
    id: 'BK-2024-1034',
    requester: 'ศศิประภา จันทร์ทอง',
    department: 'ฝ่ายขาย',
    purpose: 'พบลูกค้าที่สาขาบางนา',
    origin: 'สำนักงานใหญ่',
    destination: 'ศูนย์ฝึกอบรมบางนา',
    start: '2024-02-18T09:00:00+07:00',
    end: '2024-02-18T12:00:00+07:00',
    status: 'Pending',
    passengers: 3,
    vehicleId: 'VHC-001',
    driver: 'ปิยะพงษ์ ศรีสุข',
    notes: 'ต้องการรับลูกค้าหน้าตึกเวลา 08:40 น.',
    approvals: [
      {
        id: 'APR-1001',
        approver: 'อนุชา สุวรรณ',
        role: 'หัวหน้าฝ่ายขาย',
        status: 'Pending',
        updatedAt: '2024-02-17T15:45:00+07:00',
      },
      {
        id: 'APR-1002',
        approver: 'มณฑิรา ภาคภูมิ',
        role: 'ผู้จัดการยานพาหนะ',
        status: 'Pending',
        updatedAt: '2024-02-17T15:45:00+07:00',
      },
    ],
    history: [
      {
        id: 'HIS-1001',
        label: 'ส่งคำขอ',
        description: 'ผู้ใช้ส่งคำขอเรียบร้อย',
        timestamp: '2024-02-17T14:12:00+07:00',
        state: 'complete',
      },
      {
        id: 'HIS-1002',
        label: 'รออนุมัติ',
        description: 'รอการอนุมัติจากหัวหน้าแผนก',
        timestamp: '2024-02-17T14:12:00+07:00',
        state: 'current',
      },
      {
        id: 'HIS-1003',
        label: 'จัดสรรยานพาหนะ',
        description: 'กำลังเตรียมจัดสรรยานพาหนะและคนขับ',
        timestamp: '2024-02-18T08:00:00+07:00',
        state: 'upcoming',
      },
    ],
  },
  {
    id: 'BK-2024-1028',
    requester: 'อดิเทพ วัฒนกูล',
    department: 'วิศวกรรม',
    purpose: 'ลงพื้นที่ตรวจงาน',
    origin: 'สำนักงานใหญ่',
    destination: 'นิคมอุตสาหกรรมอมตะซิตี้',
    start: '2024-02-19T08:30:00+07:00',
    end: '2024-02-19T17:30:00+07:00',
    status: 'Approved',
    passengers: 4,
    vehicleId: 'VHC-005',
    driver: 'วีรภัทร พงศ์ไพศาล',
    approvals: [
      {
        id: 'APR-1003',
        approver: 'อัจฉรา พิมพ์สอาด',
        role: 'หัวหน้าวิศวกรรม',
        status: 'Approved',
        updatedAt: '2024-02-16T09:20:00+07:00',
        comment: 'อนุมัติเรียบร้อย เตรียมเอกสารความปลอดภัยด้วย',
      },
      {
        id: 'APR-1004',
        approver: 'มณฑิรา ภาคภูมิ',
        role: 'ผู้จัดการยานพาหนะ',
        status: 'Approved',
        updatedAt: '2024-02-16T11:05:00+07:00',
      },
    ],
    history: [
      {
        id: 'HIS-1004',
        label: 'ส่งคำขอ',
        description: 'ผู้ใช้ส่งคำขอเรียบร้อย',
        timestamp: '2024-02-15T16:50:00+07:00',
        state: 'complete',
      },
      {
        id: 'HIS-1005',
        label: 'อนุมัติแล้ว',
        description: 'ได้รับการอนุมัติทั้งหมด',
        timestamp: '2024-02-16T11:05:00+07:00',
        state: 'complete',
      },
      {
        id: 'HIS-1006',
        label: 'เตรียมยานพาหนะ',
        description: 'กำลังจัดเตรียมเอกสารและตรวจสภาพรถ',
        timestamp: '2024-02-18T16:00:00+07:00',
        state: 'current',
      },
      {
        id: 'HIS-1007',
        label: 'ออกเดินทาง',
        description: 'ออกเดินทางตรงเวลา',
        timestamp: '2024-02-19T08:30:00+07:00',
        state: 'upcoming',
      },
    ],
  },
  {
    id: 'BK-2024-1012',
    requester: 'จารุวรรณ ทองใบ',
    department: 'ฝ่ายบุคคล',
    purpose: 'จัดกิจกรรมอบรมภายใน',
    origin: 'ศูนย์ฝึกอบรมบางนา',
    destination: 'รีสอร์ทพัทยา',
    start: '2024-02-22T06:30:00+07:00',
    end: '2024-02-22T20:00:00+07:00',
    status: 'Rejected',
    passengers: 10,
    vehicleId: 'VHC-002',
    driver: 'กิตติภพ คุณากร',
    notes: 'ต้องการรถตู้ 2 คัน',
    approvals: [
      {
        id: 'APR-1005',
        approver: 'ชุติกาญจน์ เกษมสุข',
        role: 'ผู้อำนวยการฝ่ายบุคคล',
        status: 'Rejected',
        updatedAt: '2024-02-17T10:15:00+07:00',
        comment: 'โปรดปรับจำนวนผู้โดยสารและแผนการเดินทาง',
      },
    ],
    history: [
      {
        id: 'HIS-1008',
        label: 'ส่งคำขอ',
        description: 'ผู้ใช้ส่งคำขอเรียบร้อย',
        timestamp: '2024-02-14T09:00:00+07:00',
        state: 'complete',
      },
      {
        id: 'HIS-1009',
        label: 'ถูกปฏิเสธ',
        description: 'คำขอถูกปฏิเสธจากผู้อนุมัติ',
        timestamp: '2024-02-17T10:15:00+07:00',
        state: 'current',
      },
      {
        id: 'HIS-1010',
        label: 'แก้ไขและส่งใหม่',
        description: 'รอการปรับปรุงรายละเอียดเพื่อนำเสนออีกครั้ง',
        timestamp: '2024-02-18T09:30:00+07:00',
        state: 'upcoming',
      },
    ],
  },
];

export const managerPendingApprovals = [
  {
    id: 'BK-2024-1041',
    requester: 'พัชรินทร์ เกียรติสุข',
    department: 'การเงิน',
    destination: 'ธนาคารแห่งประเทศไทย',
    start: '2024-02-20T10:00:00+07:00',
    end: '2024-02-20T13:30:00+07:00',
    passengers: 2,
    urgency: 'สูง',
    vehicleType: 'Sedan',
    notes: 'ต้องการเอกสารสำรอง',
  },
  {
    id: 'BK-2024-1042',
    requester: 'วรเมธ จันทรวงศ์',
    department: 'พัฒนาธุรกิจ',
    destination: 'สนามบินดอนเมือง',
    start: '2024-02-21T05:30:00+07:00',
    end: '2024-02-21T09:30:00+07:00',
    passengers: 3,
    urgency: 'ปกติ',
    vehicleType: 'SUV',
    notes: 'ต้องรับผู้บริหารจากต่างประเทศ',
  },
  {
    id: 'BK-2024-1043',
    requester: 'ลัดดาวัลย์ รัตนพงษ์',
    department: 'การตลาด',
    destination: 'ห้างสรรพสินค้าเซ็นทรัลเวิลด์',
    start: '2024-02-19T14:00:00+07:00',
    end: '2024-02-19T17:00:00+07:00',
    passengers: 4,
    urgency: 'ด่วนมาก',
    vehicleType: 'Van',
    notes: 'เตรียมอุปกรณ์บูธและเอกสารประชาสัมพันธ์',
  },
];
