"use client";

import { useMemo } from 'react';

import {
  CalendarDays,
  Car,
  CheckCircle2,
  ClipboardList,
  Clock3,
  History,
  MailPlus,
} from 'lucide-react';

import { AuthUser } from '@/context/AuthContext';

import { CardGrid, QuickActionButton, SectionCard, StatCard, StatusBadge } from './shared';

interface RequesterDashboardProps {
  user: AuthUser;
}

interface BookingHistoryItem {
  id: string;
  vehicle: string;
  period: string;
  purpose: string;
  status: string;
}

export function RequesterDashboard({ user }: RequesterDashboardProps) {
  const bookingHistory = useMemo<BookingHistoryItem[]>(
    () => [
      {
        id: 'BK-2024-1034',
        vehicle: 'Toyota Camry - ทะเบียน 3XX-1234',
        period: '12 ก.พ. 2567 เวลา 09:00 - 12:00',
        purpose: 'ประชุมลูกค้าที่สาขาบางนา',
        status: 'Approved',
      },
      {
        id: 'BK-2024-1028',
        vehicle: 'Hyundai H1 - ทะเบียน 2BA-8899',
        period: '8 ก.พ. 2567 เวลา 13:00 - 17:30',
        purpose: 'กิจกรรมฝึกอบรมพนักงาน',
        status: 'Completed',
      },
      {
        id: 'BK-2024-1012',
        vehicle: 'Toyota Fortuner - ทะเบียน 4XZ-4477',
        period: '1 ก.พ. 2567 เวลา 08:30 - 16:00',
        purpose: 'ลงพื้นที่สำรวจโครงการ',
        status: 'Rejected',
      },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      <CardGrid>
        <StatCard
          label="คำขอที่กำลังรอ"
          value="2 รายการ"
          icon={Clock3}
          accent="amber"
          trend={{ value: '+1', description: 'จากสัปดาห์ก่อน', direction: 'up' }}
        />
        <StatCard
          label="คำขออนุมัติล่าสุด"
          value="4 รายการ"
          icon={CheckCircle2}
          accent="emerald"
          trend={{ value: '100%', description: 'อัตราการอนุมัติ', direction: 'steady' }}
        />
        <StatCard
          label="การใช้งานเดือนนี้"
          value="18 ชั่วโมง"
          icon={Car}
          accent="primary"
          trend={{ value: '+12%', description: 'เทียบกับเดือนก่อน', direction: 'up' }}
        />
        <StatCard
          label="คำขอยกเลิก"
          value="0 รายการ"
          icon={History}
          accent="sky"
          trend={{ value: '0', description: 'เดือนนี้', direction: 'steady' }}
        />
      </CardGrid>

      <SectionCard
        title="การดำเนินการด่วน"
        description="เข้าถึงฟังก์ชันยอดนิยมเพื่อเริ่มคำขอใหม่หรือดูสถานะล่าสุด"
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <QuickActionButton
            label="สร้างคำขอจองรถ"
            description="เริ่มแบบฟอร์มคำขอใหม่ พร้อมรายละเอียดการเดินทาง"
            icon={MailPlus}
            href="/bookings/new"
            tone="primary"
          />
          <QuickActionButton
            label="จองรถแบบด่วน"
            description="เลือกจากรถที่ว่างในอีก 24 ชั่วโมง"
            icon={CalendarDays}
            href="/bookings/express"
            tone="sky"
          />
          <QuickActionButton
            label="ดูปฏิทินการใช้งาน"
            description="ตรวจสอบความพร้อมของรถในทีม"
            icon={ClipboardList}
            href="/calendar"
            tone="violet"
          />
          <QuickActionButton
            label="คู่มือและนโยบาย"
            description="ข้อกำหนดการใช้รถและขั้นตอนสำคัญ"
            icon={History}
            href="/knowledge-base/policies"
            tone="amber"
          />
        </div>
      </SectionCard>

      <SectionCard title="ประวัติการจองล่าสุด" description={`ติดตามสถานะคำขอของ ${user.fullName}`}>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider text-gray-500">
                <th className="pb-3 pr-4 font-medium">หมายเลขคำขอ</th>
                <th className="pb-3 pr-4 font-medium">รถที่ใช้</th>
                <th className="pb-3 pr-4 font-medium">ช่วงเวลา</th>
                <th className="pb-3 pr-4 font-medium">วัตถุประสงค์</th>
                <th className="pb-3 font-medium">สถานะ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {bookingHistory.map((item) => (
                <tr key={item.id} className="align-top">
                  <td className="py-3 pr-4 font-medium text-gray-900">{item.id}</td>
                  <td className="py-3 pr-4 text-gray-600">{item.vehicle}</td>
                  <td className="py-3 pr-4 text-gray-600">{item.period}</td>
                  <td className="py-3 pr-4 text-gray-600">{item.purpose}</td>
                  <td className="py-3"><StatusBadge status={item.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}
