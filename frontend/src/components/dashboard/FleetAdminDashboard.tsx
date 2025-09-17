"use client";

import { useMemo } from 'react';

import {
  AlertTriangle,
  BarChart3,
  CalendarCheck2,
  Fuel,
  Gauge,
  MapPin,
  Settings2,
  Truck,
  Wrench,
} from 'lucide-react';

import { AuthUser } from '@/context/AuthContext';

import { CardGrid, EmptyState, QuickActionButton, SectionCard, StatCard, StatusBadge } from './shared';

interface FleetAdminDashboardProps {
  user: AuthUser;
}

interface FleetResourceItem {
  id: string;
  label: string;
  status: string;
  nextAction: string;
  responsible: string;
}

interface MaintenanceScheduleItem {
  id: string;
  vehicle: string;
  schedule: string;
  status: string;
}

export function FleetAdminDashboard({ user }: FleetAdminDashboardProps) {
  const resourceList = useMemo<FleetResourceItem[]>(
    () => [
      {
        id: 'VH-1020',
        label: 'Toyota Commuter - 1นข 1122',
        status: 'พร้อมใช้งาน',
        nextAction: 'ตรวจสอบ GPS & เชื้อเพลิง (85%)',
        responsible: 'สถาพร ธนศักดิ์',
      },
      {
        id: 'VH-1008',
        label: 'Isuzu D-Max - 3กธ 4477',
        status: 'อยู่ระหว่างบำรุงรักษา',
        nextAction: 'ซ่อมระบบแอร์ กำหนดเสร็จ 15 ก.พ.',
        responsible: 'หทัยชนก หงษ์ทอง',
      },
      {
        id: 'VH-0999',
        label: 'Mitsubishi Pajero Sport - 8ขค 9191',
        status: 'ต้องตรวจสอบ',
        nextAction: 'รายงานการแจ้งเตือนเครื่องยนต์จาก IoT',
        responsible: 'พรเทพ แสงทอง',
      },
    ],
    [],
  );

  const maintenanceSchedules = useMemo<MaintenanceScheduleItem[]>(
    () => [
      {
        id: 'MT-2024-021',
        vehicle: 'Toyota Fortuner - 4XZ 4477',
        schedule: 'กำหนด 14 ก.พ. 2567',
        status: 'Scheduled',
      },
      {
        id: 'MT-2024-018',
        vehicle: 'Hyundai Staria - 5กพ 3355',
        schedule: 'ดำเนินการ 10 ก.พ. 2567',
        status: 'Completed',
      },
      {
        id: 'MT-2024-017',
        vehicle: 'Isuzu MU-X - 9ขฉ 2210',
        schedule: 'รออะไหล่ (17 ก.พ. 2567)',
        status: 'Pending',
      },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      <CardGrid>
        <StatCard
          label="อัตราการใช้งานยานพาหนะ"
          value="92%"
          icon={Gauge}
          accent="primary"
          trend={{ value: '+4%', description: 'เทียบกับเดือนก่อน', direction: 'up' }}
        />
        <StatCard
          label="รถที่ไม่พร้อมใช้งาน"
          value="3 คัน"
          icon={AlertTriangle}
          accent="rose"
          trend={{ value: '-1', description: 'ดีขึ้นจากสัปดาห์ก่อน', direction: 'down' }}
        />
        <StatCard
          label="งานบำรุงรักษาสัปดาห์นี้"
          value="7 งาน"
          icon={Wrench}
          accent="amber"
          trend={{ value: 'อยู่ระหว่าง 3 งาน', direction: 'steady' }}
        />
        <StatCard
          label="เชื้อเพลิงเฉลี่ย"
          value="78%"
          icon={Fuel}
          accent="emerald"
          trend={{ value: '-5%', description: 'ต้องเติม 4 คัน', direction: 'down' }}
        />
      </CardGrid>

      <SectionCard
        title="รายการยานพาหนะและทรัพยากร"
        description="ภาพรวมสถานะรถและงานถัดไป"
        actions={<button className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50">จัดการทรัพยากร</button>}
      >
        <div className="space-y-4">
          {resourceList.map((item) => (
            <div key={item.id} className="rounded-xl border border-gray-100 bg-white/80 p-4 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-gray-900">{item.label}</p>
                  <p className="text-xs text-gray-500">{item.id}</p>
                  <p className="mt-2 text-xs text-gray-500">ผู้รับผิดชอบ: {item.responsible}</p>
                </div>
                <div className="text-right">
                  <StatusBadge status={item.status} />
                  <p className="mt-2 text-xs text-gray-500">{item.nextAction}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="กำหนดการบำรุงรักษา"
        description="ติดตามสถานะงานซ่อมและการตรวจสอบประจำ"
        actions={<button className="rounded-lg border border-primary-200 px-3 py-1.5 text-xs font-medium text-primary-600">แสดงบนปฏิทิน</button>}
      >
        {maintenanceSchedules.length === 0 ? (
          <EmptyState icon={CalendarCheck2} title="ยังไม่มีงานบำรุงรักษา" description="เมื่อมีการนัดหมาย ระบบจะแสดงรายละเอียดที่นี่" />
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {maintenanceSchedules.map((item) => (
              <div key={item.id} className="rounded-xl border border-gray-100 bg-white/80 p-4 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{item.vehicle}</p>
                    <p className="text-xs text-gray-500">รหัสงาน: {item.id}</p>
                    <p className="mt-2 text-xs text-gray-500">{item.schedule}</p>
                  </div>
                  <StatusBadge status={item.status} />
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="เครื่องมือสำหรับผู้ดูแลยานพาหนะ" description={`จัดการทรัพยากรและการวิเคราะห์สำหรับ ${user.fullName}`}>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <QuickActionButton
            label="เพิ่มรถคันใหม่"
            description="ลงทะเบียนข้อมูลรถพร้อมระบบติดตาม"
            icon={Truck}
            href="/fleet/new-vehicle"
          />
          <QuickActionButton
            label="จัดตารางบำรุงรักษา"
            description="วางแผนป้องกันความขัดข้อง"
            icon={Settings2}
            href="/fleet/maintenance"
            tone="amber"
          />
          <QuickActionButton
            label="วิเคราะห์การใช้งาน"
            description="ดูสถิติและแนวโน้มการใช้รถ"
            icon={BarChart3}
            href="/reports/fleet-analytics"
            tone="violet"
          />
          <QuickActionButton
            label="ติดตาม GPS"
            description="ตรวจสอบตำแหน่งปัจจุบันและเส้นทาง"
            icon={MapPin}
            href="/fleet/gps-monitoring"
            tone="sky"
          />
        </div>
      </SectionCard>

      <SectionCard title="การแจ้งเตือนจากระบบ IoT" description="ข้อมูลสถานะที่ส่งเข้ามาล่าสุด">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-gray-100 bg-white/80 p-4 shadow-sm">
            <p className="text-sm font-semibold text-gray-900">สัญญาณเตือนเครื่องยนต์</p>
            <p className="mt-2 text-xs text-gray-500">Mitsubishi Pajero Sport - เกิดการสั่นสะเทือนผิดปกติ</p>
            <p className="mt-4 text-xs font-medium text-rose-600">แจ้งเตือนเมื่อ 09:12 น.</p>
          </div>
          <div className="rounded-xl border border-gray-100 bg-white/80 p-4 shadow-sm">
            <p className="text-sm font-semibold text-gray-900">ระดับเชื้อเพลิงต่ำ</p>
            <p className="mt-2 text-xs text-gray-500">Toyota Commuter - ปริมาณต่ำกว่า 20%</p>
            <p className="mt-4 text-xs font-medium text-amber-600">แจ้งเตือนเมื่อ 08:45 น.</p>
          </div>
          <div className="rounded-xl border border-gray-100 bg-white/80 p-4 shadow-sm">
            <p className="text-sm font-semibold text-gray-900">ยืนยันการบำรุงรักษาเสร็จสิ้น</p>
            <p className="mt-2 text-xs text-gray-500">Hyundai Staria - อัปเดตโดยหทัยชนก หงษ์ทอง</p>
            <p className="mt-4 text-xs font-medium text-emerald-600">แจ้งเตือนเมื่อ 07:20 น.</p>
          </div>
          <div className="rounded-xl border border-gray-100 bg-white/80 p-4 shadow-sm">
            <p className="text-sm font-semibold text-gray-900">อัปเดตซอฟต์แวร์ GPS</p>
            <p className="mt-2 text-xs text-gray-500">Toyota Camry - ติดตั้งสำเร็จ</p>
            <p className="mt-4 text-xs font-medium text-primary-600">แจ้งเตือนเมื่อ 06:50 น.</p>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}
