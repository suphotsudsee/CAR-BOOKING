"use client";

import { useEffect, useMemo, useState } from 'react';

import { useRouter } from 'next/navigation';

import { Activity, BellRing, ClipboardCheck, Gauge, RefreshCcw, Timer, UsersRound } from 'lucide-react';

import {
  CardGrid,
  DriverDashboard,
  FleetAdminDashboard,
  ManagerDashboard,
  RequesterDashboard,
  StatCard,
} from '@/components/dashboard';
import { SectionCard } from '@/components/dashboard/shared';
import { NotificationItem, useNotificationCenter } from '@/components/notifications/useNotificationCenter';
import { useAuth, USER_ROLES, type UserRole } from '@/context/AuthContext';

const roleTitles: Record<UserRole, string> = {
  requester: 'แดชบอร์ดผู้ขอใช้รถ',
  manager: 'แดชบอร์ดผู้จัดการ',
  fleet_admin: 'แดชบอร์ดผู้ดูแลยานพาหนะ',
  driver: 'แดชบอร์ดคนขับ',
  auditor: 'แดชบอร์ดผู้ตรวจสอบ',
};

const roleDescriptions: Record<UserRole, string> = {
  requester: 'ติดตามสถานะคำขอ ดูประวัติการจอง และสร้างคำขอใหม่ได้ทันที',
  manager: 'จัดการคิวอนุมัติ ติดตามการใช้งานของทีม และวิเคราะห์ประสิทธิภาพ',
  fleet_admin: 'ดูภาพรวมทรัพยากรยานพาหนะ ตรวจสอบงานบำรุงรักษา และวิเคราะห์ข้อมูล',
  driver: 'ตรวจสอบงานที่ได้รับมอบหมาย เช็กอิน/เช็กเอาต์ และรายงานผลการปฏิบัติงาน',
  auditor: 'ตรวจสอบประวัติและรายงานการใช้งานเพื่อสนับสนุนการตรวจสอบ',
};

interface LiveStatsState {
  utilisation: number;
  pendingApprovals: number;
  activeDrivers: number;
  todaysTrips: number;
}

function useLiveStats(initialising = false): LiveStatsState {
  const [stats, setStats] = useState<LiveStatsState>({
    utilisation: 86,
    pendingApprovals: 7,
    activeDrivers: 12,
    todaysTrips: 28,
  });

  useEffect(() => {
    if (initialising) return;
    const interval = setInterval(() => {
      setStats((previous) => {
        const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);
        return {
          utilisation: clamp(previous.utilisation + (Math.random() * 4 - 2), 70, 98),
          pendingApprovals: clamp(previous.pendingApprovals + Math.round(Math.random() * 2 - 1), 0, 25),
          activeDrivers: clamp(previous.activeDrivers + Math.round(Math.random() * 3 - 1), 4, 40),
          todaysTrips: clamp(previous.todaysTrips + Math.round(Math.random() * 4 - 1), 5, 60),
        };
      });
    }, 8000);

    return () => {
      clearInterval(interval);
    };
  }, [initialising]);

  return stats;
}

function NotificationWidget({ notifications, unreadCount, loading, error, onRefresh }: {
  notifications: NotificationItem[];
  unreadCount: number;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  const latest = notifications.slice(0, 4);

  return (
    <SectionCard
      title="การแจ้งเตือนล่าสุด"
      description="ติดตามการอนุมัติและข้อความสำคัญแบบเรียลไทม์"
      actions={
        <button
          type="button"
          onClick={onRefresh}
          className="inline-flex items-center gap-2 rounded-lg border border-primary-200 px-3 py-1.5 text-xs font-medium text-primary-600 hover:bg-primary-50"
        >
          <RefreshCcw className="h-3.5 w-3.5" /> รีเฟรช
        </button>
      }
    >
      <div className="flex items-center justify-between rounded-xl border border-dashed border-gray-300 bg-white/70 p-4">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
            <BellRing className="h-5 w-5" />
          </span>
          <div>
            <p className="text-sm font-semibold text-gray-900">แจ้งเตือนที่ยังไม่ได้อ่าน</p>
            <p className="text-xs text-gray-500">ระบบจะอัปเดตทันทีเมื่อมีการอนุมัติหรือข้อความใหม่</p>
          </div>
        </div>
        <span className="text-3xl font-bold text-primary-600">{unreadCount}</span>
      </div>

      {error && <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600">{error}</p>}

      <div className="space-y-3">
        {loading && <p className="text-xs text-gray-500">กำลังโหลดข้อมูล...</p>}
        {!loading && latest.length === 0 && (
          <p className="rounded-lg border border-gray-200 bg-white/70 px-3 py-3 text-xs text-gray-500">ยังไม่มีการแจ้งเตือนใหม่</p>
        )}
        {latest.map((item) => (
          <div key={item.id} className="rounded-xl border border-gray-100 bg-white/80 p-4 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-gray-900">{item.title}</p>
                <p className="mt-1 text-xs text-gray-500">{item.message}</p>
              </div>
              <span className="text-xs text-gray-400">{new Date(item.createdAt).toLocaleString('th-TH')}</span>
            </div>
            {item.category && <p className="mt-2 text-xs font-medium text-primary-600">ประเภท: {item.category}</p>}
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, initializing } = useAuth();
  const liveStats = useLiveStats(initializing);
  const { notifications, unreadCount, loading, error, refresh } = useNotificationCenter();

  const derivedRealtime = useMemo(() => {
    const onTimeRate = Math.min(99, Math.max(90, Math.round(liveStats.utilisation + 8)));
    const avgResponse = Math.max(0.8, 4 - liveStats.utilisation / 60).toFixed(1);
    const readiness = Math.round(liveStats.utilisation);
    const notificationDelta = Math.max(unreadCount + 2, Math.round(unreadCount * 1.4 + 1));
    return {
      onTimeRate,
      avgResponse,
      readiness,
      notificationDelta,
    };
  }, [liveStats.utilisation, unreadCount]);

  useEffect(() => {
    if (!initializing && !isAuthenticated) {
      router.push('/login');
    }
  }, [initializing, isAuthenticated, router]);

  const roleTitle = user ? roleTitles[user.role] : 'แดชบอร์ด';
  const roleDescription = user ? roleDescriptions[user.role] : 'กำลังโหลดข้อมูลผู้ใช้';

  const dashboardContent = useMemo(() => {
    if (!user) return null;
    switch (user.role) {
      case USER_ROLES.REQUESTER:
        return <RequesterDashboard user={user} />;
      case USER_ROLES.MANAGER:
        return <ManagerDashboard user={user} />;
      case USER_ROLES.FLEET_ADMIN:
        return <FleetAdminDashboard user={user} />;
      case USER_ROLES.DRIVER:
        return <DriverDashboard user={user} />;
      default:
        return (
          <SectionCard title="แดชบอร์ดสำหรับผู้ตรวจสอบ" description="อยู่ระหว่างการพัฒนา">
            <p className="text-sm text-gray-600">
              บทบาทผู้ตรวจสอบจะได้รับแดชบอร์ดเฉพาะสำหรับการตรวจสอบประวัติและการปฏิบัติตามข้อกำหนดในเร็ว ๆ นี้
            </p>
          </SectionCard>
        );
    }
  }, [user]);

  if (initializing || (!user && isAuthenticated)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-50 to-secondary-50">
        <div className="rounded-2xl border border-primary-100 bg-white/70 px-6 py-4 text-sm text-gray-500 shadow-sm">
          กำลังเตรียมแดชบอร์ด...
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50/80 via-white to-secondary-50/70 py-10">
      <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="rounded-3xl border border-primary-100/60 bg-white/80 p-6 shadow-lg backdrop-blur">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-primary-600">สวัสดี {user.fullName}</p>
              <h1 className="text-3xl font-semibold text-gray-900">{roleTitle}</h1>
              <p className="text-sm text-gray-600">{roleDescription}</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex items-center gap-3 rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4">
                <Gauge className="h-5 w-5 text-emerald-600" />
                <div>
                  <p className="text-xs uppercase tracking-wide text-emerald-600">อัตราการใช้งาน</p>
                  <p className="text-xl font-semibold text-emerald-700">{liveStats.utilisation.toFixed(1)}%</p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-2xl border border-amber-100 bg-amber-50/70 p-4">
                <Timer className="h-5 w-5 text-amber-600" />
                <div>
                  <p className="text-xs uppercase tracking-wide text-amber-600">คำขอรอดำเนินการ</p>
                  <p className="text-xl font-semibold text-amber-700">{liveStats.pendingApprovals}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-2xl border border-sky-100 bg-sky-50/70 p-4">
                <UsersRound className="h-5 w-5 text-sky-600" />
                <div>
                  <p className="text-xs uppercase tracking-wide text-sky-600">คนขับที่กำลังทำงาน</p>
                  <p className="text-xl font-semibold text-sky-700">{liveStats.activeDrivers}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-2xl border border-violet-100 bg-violet-50/70 p-4">
                <ClipboardCheck className="h-5 w-5 text-violet-600" />
                <div>
                  <p className="text-xs uppercase tracking-wide text-violet-600">งานในวันนี้</p>
                  <p className="text-xl font-semibold text-violet-700">{liveStats.todaysTrips}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_360px] xl:grid-cols-[minmax(0,1fr)_380px]">
          <main className="space-y-8">{dashboardContent}</main>
          <aside className="space-y-6">
            <NotificationWidget
              notifications={notifications}
              unreadCount={unreadCount}
              loading={loading}
              error={error}
              onRefresh={() => {
                void refresh();
              }}
            />

            <SectionCard title="สถิติระบบแบบเรียลไทม์" description="อัปเดตทุกไม่กี่วินาทีเพื่อช่วยตัดสินใจได้เร็วขึ้น">
              <CardGrid className="grid-cols-1 gap-3 sm:grid-cols-2">
                <StatCard
                  label="อัตราความตรงเวลา"
                  value={`${derivedRealtime.onTimeRate}%`}
                  icon={Activity}
                  accent="emerald"
                  trend={{ value: '+1.2%', description: 'จากชั่วโมงที่ผ่านมา', direction: 'up' }}
                />
                <StatCard
                  label="เวลาตอบสนองเฉลี่ย"
                  value={`${derivedRealtime.avgResponse} ชม.`}
                  icon={Timer}
                  accent="primary"
                  trend={{ value: '-8 นาที', description: 'เร็วขึ้น', direction: 'down' }}
                />
                <StatCard
                  label="ความพร้อมของยานพาหนะ"
                  value={`${derivedRealtime.readiness}%`}
                  icon={Gauge}
                  accent="sky"
                  trend={{ value: '+2%', description: 'จากเมื่อวาน', direction: 'up' }}
                />
                <StatCard
                  label="การแจ้งเตือนใหม่"
                  value={`${unreadCount} รายการ`}
                  icon={BellRing}
                  accent="violet"
                  trend={{ value: `+${derivedRealtime.notificationDelta}`, description: 'ในรอบ 24 ชม.', direction: 'up' }}
                />
              </CardGrid>
            </SectionCard>
          </aside>
        </div>
      </div>
    </div>
  );
}
