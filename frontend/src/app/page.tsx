"use client";

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { AppShell } from '@/components/layout/AppShell';
import { MobileNotificationDrawer } from '@/components/layout/MobileNotificationDrawer';
import { NotificationCenter } from '@/components/notifications/NotificationCenter';
import { useNotificationCenter } from '@/components/notifications/useNotificationCenter';
import { useAuth } from '@/context/AuthContext';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, user, logout } = useAuth();
  const notificationController = useNotificationCenter();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const guestContent = (
    <div className="flex flex-col gap-6">
      <section className="rounded-3xl bg-white p-6 shadow-xl shadow-primary-100/60 sm:p-10">
        <div className="flex flex-col gap-4">
          <span className="inline-flex max-w-max items-center gap-2 rounded-full bg-primary-100 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-primary-700">
            จองรถง่ายในคลิกเดียว
          </span>
          <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">
            ระบบจองรถสำนักงานพร้อมสำหรับการใช้งานบนมือถือของคุณ
          </h1>
          <p className="text-base leading-relaxed text-slate-600">
            จัดการคำขอ ใช้กระบวนการอนุมัติหลายขั้นตอน และตรวจสอบสถานะได้ทุกที่ รองรับการใช้งานออฟไลน์และแจ้งเตือนแบบพุชทันทีเมื่อมีการอัปเดต
          </p>
        </div>
        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          <Link href="/login" className="inline-flex items-center justify-center rounded-full bg-primary-600 px-6 py-4 text-base font-semibold text-white shadow-lg shadow-primary-300 transition hover:bg-primary-700">
            เข้าสู่ระบบเพื่อเริ่มจองรถ
          </Link>
          <Link href="/register" className="inline-flex items-center justify-center rounded-full border border-primary-200 px-6 py-4 text-base font-semibold text-primary-600 transition hover:bg-primary-50">
            สมัครใช้งานระบบ
          </Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        {[
          {
            title: 'สร้างคำขอได้รวดเร็ว',
            description: 'แบบฟอร์มอัจฉริยะช่วยกรอกข้อมูลเดิมและลดการพิมพ์ซ้ำ พร้อมตรวจสอบความพร้อมของรถโดยอัตโนมัติ',
          },
          {
            title: 'ติดตามสถานะแบบเรียลไทม์',
            description: 'รู้ทันทีเมื่อผู้จัดการอนุมัติหรือปฏิเสธ พร้อมประวัติคำขอที่เข้าถึงได้ทุกที่',
          },
          {
            title: 'รองรับการใช้งานออฟไลน์',
            description: 'บันทึกคำขอไว้ล่วงหน้าแม้ไม่มีอินเทอร์เน็ต ระบบจะส่งให้อัตโนมัติเมื่อกลับมาออนไลน์',
          },
          {
            title: 'ปลอดภัยสำหรับองค์กร',
            description: 'ข้อมูลทุกคำขอถูกเข้ารหัส พร้อมระบบสิทธิ์การใช้งานตามบทบาทและบันทึกการเปลี่ยนแปลง',
          },
        ].map((feature) => (
          <article key={feature.title} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">{feature.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">{feature.description}</p>
          </article>
        ))}
      </section>
    </div>
  );

  const authenticatedContent = (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
      <section className="flex flex-col gap-6">
        <div className="rounded-3xl bg-white p-6 shadow-xl shadow-primary-100/60 sm:p-10">
          <div className="flex flex-col gap-4">
            <span className="inline-flex max-w-max items-center gap-2 rounded-full bg-emerald-100 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-emerald-700">
              พร้อมใช้งาน
            </span>
            <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">ยินดีต้อนรับกลับ {user?.fullName}</h1>
            <p className="text-sm font-medium text-primary-600">
              บทบาทของคุณ: <span className="font-semibold text-primary-700">{user?.role}</span>
            </p>
            <p className="text-base leading-relaxed text-slate-600">
              ติดตามคำขอที่รอดำเนินการ ตรวจสอบตารางการใช้รถล่วงหน้า และรับการแจ้งเตือนอัตโนมัติแม้ออฟไลน์
            </p>
          </div>
          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            <Link href="/bookings/new" className="flex flex-col items-center gap-2 rounded-2xl bg-primary-600 px-4 py-5 text-center text-sm font-semibold text-white shadow-lg shadow-primary-300 transition hover:bg-primary-700">
              <span className="text-lg">➕</span>
              สร้างคำขอใหม่
            </Link>
            <Link href="/calendar" className="flex flex-col items-center gap-2 rounded-2xl border border-primary-200 bg-primary-50 px-4 py-5 text-center text-sm font-semibold text-primary-600 transition hover:bg-primary-100">
              <span className="text-lg">📅</span>
              ปฏิทินการใช้รถ
            </Link>
            <Link href="/profile" className="flex flex-col items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-5 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
              <span className="text-lg">👤</span>
              จัดการโปรไฟล์
            </Link>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm sm:p-8">
          <h2 className="text-lg font-semibold text-slate-900">สิ่งที่ต้องทำต่อไป</h2>
          <ul className="mt-4 space-y-4 text-sm text-slate-600">
            <li className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">ตรวจสอบคำขอที่รออนุมัติจากทีมงาน</li>
            <li className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">บันทึกแผนการใช้รถสำหรับสัปดาห์หน้า</li>
            <li className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">อัปเดตข้อมูลโปรไฟล์สำหรับการติดต่อฉุกเฉิน</li>
          </ul>
        </div>
      </section>

      <section className="hidden lg:block">
        <NotificationCenter controller={notificationController} />
      </section>
    </div>
  );

  return (
    <>
      <AppShell
        isAuthenticated={isAuthenticated}
        fullName={user?.fullName}
        unreadCount={notificationController.unreadCount}
        onOpenNotifications={() => setDrawerOpen(true)}
        onLogout={handleLogout}
      >
        {isAuthenticated ? authenticatedContent : guestContent}
      </AppShell>

      <MobileNotificationDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <NotificationCenter controller={notificationController} />
      </MobileNotificationDrawer>
    </>
  );
}
