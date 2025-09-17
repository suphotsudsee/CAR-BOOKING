"use client";

import { useMemo, useState } from 'react';

import {
  CalendarCheck,
  CheckCircle,
  Clock4,
  LogIn,
  LogOut,
  MapPinned,
  Route,
  SteeringWheel,
  UserCheck,
} from 'lucide-react';

import { AuthUser } from '@/context/AuthContext';

import { CardGrid, EmptyState, QuickActionButton, SectionCard, StatCard, TimelineItem } from './shared';

interface DriverDashboardProps {
  user: AuthUser;
}

interface JobAssignmentItem {
  id: string;
  destination: string;
  schedule: string;
  requester: string;
  status: string;
}

export function DriverDashboard({ user }: DriverDashboardProps) {
  const [checkedIn, setCheckedIn] = useState(false);

  const jobAssignments = useMemo<JobAssignmentItem[]>(
    () => [
      {
        id: 'JOB-2024-117',
        destination: 'สำนักงานใหญ่บางนา',
        schedule: '12 ก.พ. 2567 · 08:00 - 11:30 น.',
        requester: 'สุกัญญา ชาญชัย',
        status: 'Scheduled',
      },
      {
        id: 'JOB-2024-118',
        destination: 'โรงงานผลิต จ.ระยอง',
        schedule: '12 ก.พ. 2567 · 13:30 - 18:00 น.',
        requester: 'ธีรเดช พงษ์ไพบูลย์',
        status: 'Scheduled',
      },
      {
        id: 'JOB-2024-110',
        destination: 'สนามบินสุวรรณภูมิ',
        schedule: '11 ก.พ. 2567 · 05:30 - 09:00 น.',
        requester: 'ณัฐพงศ์ เกตุแก้ว',
        status: 'Completed',
      },
    ],
    [],
  );

  const handleCheckIn = () => {
    setCheckedIn(true);
  };

  const handleCheckOut = () => {
    setCheckedIn(false);
  };

  return (
    <div className="space-y-6">
      <CardGrid>
        <StatCard
          label="งานวันนี้"
          value="2 งาน"
          icon={SteeringWheel}
          accent="primary"
          trend={{ value: '+1', description: 'งานเพิ่มเติม', direction: 'up' }}
        />
        <StatCard
          label="งานที่เสร็จสิ้น"
          value="18 งาน"
          icon={CheckCircle}
          accent="emerald"
          trend={{ value: '95%', description: 'ตรงเวลา', direction: 'steady' }}
        />
        <StatCard
          label="เวลาว่าง"
          value="4 ชม."
          icon={Clock4}
          accent="sky"
          trend={{ value: '-1 ชม.', description: 'จากแผน', direction: 'down' }}
        />
        <StatCard
          label="ระยะทางเดือนนี้"
          value="1,240 กม."
          icon={Route}
          accent="violet"
          trend={{ value: '+8%', description: 'เทียบกับเดือนก่อน', direction: 'up' }}
        />
      </CardGrid>

      <SectionCard
        title="สถานะการปฏิบัติงาน"
        description={`บันทึกการเช็กอิน/เช็กเอาต์ของ ${user.fullName}`}
        actions={
          checkedIn ? (
            <button
              type="button"
              onClick={handleCheckOut}
              className="inline-flex items-center gap-2 rounded-lg border border-rose-200 px-4 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50"
            >
              <LogOut className="h-4 w-4" />
              เช็กเอาต์
            </button>
          ) : (
            <button
              type="button"
              onClick={handleCheckIn}
              className="inline-flex items-center gap-2 rounded-lg border border-emerald-200 px-4 py-2 text-sm font-medium text-emerald-600 hover:bg-emerald-50"
            >
              <LogIn className="h-4 w-4" />
              เช็กอิน
            </button>
          )
        }
      >
        <div className="rounded-xl border border-dashed border-gray-300 bg-white/70 p-6 text-sm text-gray-600">
          <p>
            สถานะปัจจุบัน:{' '}
            <span className={checkedIn ? 'font-semibold text-emerald-600' : 'font-semibold text-gray-500'}>
              {checkedIn ? 'กำลังปฏิบัติงาน' : 'ยังไม่เริ่มงาน'}
            </span>
          </p>
          <p className="mt-2 text-xs text-gray-500">
            ระบบจะบันทึกเวลาพร้อมตำแหน่งอัตโนมัติเมื่อกดเช็กอิน/เช็กเอาต์ เพื่อให้ผู้จัดการติดตามสถานะได้แบบเรียลไทม์
          </p>
        </div>
      </SectionCard>

      <SectionCard
        title="งานที่ได้รับมอบหมาย"
        description="เช็กเส้นทางและผู้โดยสารก่อนออกเดินทาง"
      >
        {jobAssignments.length === 0 ? (
          <EmptyState icon={CalendarCheck} title="ยังไม่มีงานในวันนี้" description="เมื่อมีงานมอบหมายใหม่ ระบบจะแจ้งเตือนให้ทราบทันที" />
        ) : (
          <div className="space-y-4">
            {jobAssignments.map((item, index) => (
              <TimelineItem
                key={item.id}
                title={`${item.destination} · ${item.requester}`}
                description={item.id}
                timestamp={item.schedule}
                status={item.status}
                accent={index % 2 === 0 ? 'sky' : 'violet'}
              />
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="ตัวช่วยสำหรับคนขับ" description="รวมลิงก์ที่ใช้บ่อยสำหรับการปฏิบัติงานประจำวัน">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <QuickActionButton
            label="เริ่มนำทาง"
            description="เปิดแผนที่พร้อมเส้นทางที่ได้รับ"
            icon={MapPinned}
            href="/driver/navigation"
          />
          <QuickActionButton
            label="เช็กลิสต์ก่อนออกเดินทาง"
            description="ตรวจสอบรถและอุปกรณ์ก่อนใช้งาน"
            icon={UserCheck}
            href="/driver/checklist"
            tone="emerald"
          />
          <QuickActionButton
            label="รายงานเหตุการณ์"
            description="แจ้งเหตุขัดข้องหรืออุบัติเหตุ"
            icon={Route}
            href="/driver/incidents"
            tone="amber"
          />
          <QuickActionButton
            label="สรุปการปฏิบัติงาน"
            description="กรอกข้อมูลหลังเสร็จงาน"
            icon={CalendarCheck}
            href="/driver/daily-report"
            tone="primary"
          />
        </div>
      </SectionCard>
    </div>
  );
}
