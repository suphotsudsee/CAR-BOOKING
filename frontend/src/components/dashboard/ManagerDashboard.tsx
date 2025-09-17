"use client";

import { useMemo } from 'react';

import {
  BarChart3,
  CalendarClock,
  CheckSquare,
  ClipboardSignature,
  ClockAlert,
  ClipboardList,
  Users,
} from 'lucide-react';

import { AuthUser } from '@/context/AuthContext';

import { CardGrid, QuickActionButton, SectionCard, StatCard, TimelineItem } from './shared';

interface ManagerDashboardProps {
  user: AuthUser;
}

interface ApprovalQueueItem {
  id: string;
  requester: string;
  purpose: string;
  submittedAt: string;
  status: 'รอดำเนินการ' | 'มีการแก้ไข';
}

interface TeamUsageItem {
  teamMember: string;
  completedTrips: number;
  utilization: number;
  upcomingTrips: number;
}

export function ManagerDashboard({ user }: ManagerDashboardProps) {
  const approvalQueue = useMemo<ApprovalQueueItem[]>(
    () => [
      {
        id: 'BK-2024-1040',
        requester: 'สุทธิดา ภาคี',
        purpose: 'ตรวจเยี่ยมสาขานครราชสีมา',
        submittedAt: '12 ก.พ. 2567 08:25',
        status: 'รอดำเนินการ',
      },
      {
        id: 'BK-2024-1036',
        requester: 'ธีรเดช พงษ์ไพบูลย์',
        purpose: 'ร่วมงานประชุมคณะกรรมการ',
        submittedAt: '11 ก.พ. 2567 19:10',
        status: 'มีการแก้ไข',
      },
      {
        id: 'BK-2024-1031',
        requester: 'สุกัญญา ชาญชัย',
        purpose: 'กิจกรรม CSR ณ โรงเรียนบ้านคลองใหญ่',
        submittedAt: '11 ก.พ. 2567 10:05',
        status: 'รอดำเนินการ',
      },
    ],
    [],
  );

  const teamUsage = useMemo<TeamUsageItem[]>(
    () => [
      { teamMember: 'กนกวรรณ ทองแท้', completedTrips: 5, utilization: 78, upcomingTrips: 2 },
      { teamMember: 'กรกช วิริยะ', completedTrips: 3, utilization: 52, upcomingTrips: 1 },
      { teamMember: 'พิทักษ์ชัย จันทรา', completedTrips: 6, utilization: 88, upcomingTrips: 4 },
      { teamMember: 'ศุภกานต์ โอภาส', completedTrips: 4, utilization: 61, upcomingTrips: 2 },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      <CardGrid>
        <StatCard
          label="คำขอรออนุมัติ"
          value="5 รายการ"
          icon={ClockAlert}
          accent="amber"
          trend={{ value: '-2', description: 'จากเมื่อวาน', direction: 'down' }}
        />
        <StatCard
          label="การอนุมัติสัปดาห์นี้"
          value="18 รายการ"
          icon={CheckSquare}
          accent="emerald"
          trend={{ value: '+6%', description: 'เทียบกับสัปดาห์ก่อน', direction: 'up' }}
        />
        <StatCard
          label="เวลาตอบสนองเฉลี่ย"
          value="2 ชม. 15 นาที"
          icon={CalendarClock}
          accent="primary"
          trend={{ value: '-25 นาที', description: 'เร่งด่วนขึ้น', direction: 'down' }}
        />
        <StatCard
          label="คำขอรอข้อมูลเพิ่ม"
          value="1 รายการ"
          icon={ClipboardSignature}
          accent="violet"
          trend={{ value: '20%', description: 'ของทั้งหมด', direction: 'steady' }}
        />
      </CardGrid>

      <SectionCard
        title="คิวคำขอที่ต้องอนุมัติ"
        description="ติดตามคำขอที่ต้องดำเนินการโดยทีมของคุณ"
        actions={<button className="rounded-lg border border-primary-200 px-4 py-2 text-sm font-medium text-primary-600">ดูทั้งหมด</button>}
      >
        <div className="space-y-4">
          {approvalQueue.map((item, index) => (
            <TimelineItem
              key={item.id}
              title={`${item.id} · ${item.requester}`}
              description={item.purpose}
              timestamp={item.submittedAt}
              status={item.status}
              accent={index % 2 === 0 ? 'primary' : 'violet'}
            />
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="ภาพรวมทีมงาน"
        description={`ข้อมูลการใช้รถของทีมที่ ${user.department ?? 'สังกัดไม่ระบุ'}`}
        actions={<button className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50">ดาวน์โหลดรายงาน</button>}
      >
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider text-gray-500">
                <th className="pb-3 pr-4 font-medium">สมาชิกทีม</th>
                <th className="pb-3 pr-4 font-medium">งานที่เสร็จสิ้น</th>
                <th className="pb-3 pr-4 font-medium">อัตราการใช้งาน</th>
                <th className="pb-3 font-medium">งานข้างหน้า</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {teamUsage.map((item) => (
                <tr key={item.teamMember} className="align-top">
                  <td className="py-3 pr-4 font-medium text-gray-900">{item.teamMember}</td>
                  <td className="py-3 pr-4 text-gray-600">{item.completedTrips} งาน</td>
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-full rounded-full bg-gray-100">
                        <div className="h-2 rounded-full bg-primary-500" style={{ width: `${item.utilization}%` }} />
                      </div>
                      <span className="text-sm text-gray-600">{item.utilization}%</span>
                    </div>
                  </td>
                  <td className="py-3 text-gray-600">{item.upcomingTrips} งาน</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      <SectionCard
        title="เครื่องมือสำหรับผู้จัดการ"
        description="ฟังก์ชันที่ช่วยให้การดูแลคำขอเป็นไปอย่างราบรื่น"
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <QuickActionButton
            label="ตรวจสอบคำขอทั้งหมด"
            description="ดูคิวและอนุมัติคำขอในคลิกเดียว"
            icon={ClipboardList}
            href="/approvals"
          />
          <QuickActionButton
            label="ตั้งค่าผู้อนุมัติแทน"
            description="กำหนดผู้แทนในช่วงลาพักร้อน"
            icon={Users}
            href="/approvals/delegation"
            tone="violet"
          />
          <QuickActionButton
            label="สถิติการใช้ทีม"
            description="ดูแนวโน้มการใช้งานและการวางแผน"
            icon={BarChart3}
            href="/reports/team-usage"
            tone="emerald"
          />
          <QuickActionButton
            label="รายการติดตาม"
            description="บันทึกคำขอที่ต้องการข้อมูลเพิ่มเติม"
            icon={ClipboardSignature}
            href="/approvals/follow-ups"
            tone="amber"
          />
        </div>
      </SectionCard>
    </div>
  );
}
