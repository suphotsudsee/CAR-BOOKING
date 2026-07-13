<<<<<<< HEAD
"use client";

import Link from 'next/link';
import { useState } from 'react';

import { AppShell } from '@/components/layout/AppShell';
import { MobileNotificationDrawer } from '@/components/layout/MobileNotificationDrawer';
import { NotificationCenter } from '@/components/notifications/NotificationCenter';
import { useNotificationCenter } from '@/components/notifications/useNotificationCenter';
import { useAuth } from '@/context/AuthContext';

export default function HomePage() {
  const { isAuthenticated, user } = useAuth();
  const notificationController = useNotificationCenter();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const guestContent = (
    <div className="flex flex-col gap-6">
      <section className="rounded-3xl bg-white p-6 shadow-xl shadow-primary-100/60 sm:p-10">
        <div className="flex flex-col gap-4">
          <span className="inline-flex max-w-max items-center gap-2 rounded-full bg-primary-100 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-primary-700">
            เธเธญเธเธฃเธ–เธเนเธฒเธขเนเธเธเธฅเธดเธเน€เธ”เธตเธขเธง
          </span>
          <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">
            เธฃเธฐเธเธเธเธญเธเธฃเธ–เธชเธณเธเธฑเธเธเธฒเธเธเธฃเนเธญเธกเธชเธณเธซเธฃเธฑเธเธเธฒเธฃเนเธเนเธเธฒเธเธเธเธกเธทเธญเธ–เธทเธญเธเธญเธเธเธธเธ“
          </h1>
          <p className="text-base leading-relaxed text-slate-600">
            เธเธฑเธ”เธเธฒเธฃเธเธณเธเธญ เนเธเนเธเธฃเธฐเธเธงเธเธเธฒเธฃเธญเธเธธเธกเธฑเธ•เธดเธซเธฅเธฒเธขเธเธฑเนเธเธ•เธญเธ เนเธฅเธฐเธ•เธฃเธงเธเธชเธญเธเธชเธ–เธฒเธเธฐเนเธ”เนเธ—เธธเธเธ—เธตเน เธฃเธญเธเธฃเธฑเธเธเธฒเธฃเนเธเนเธเธฒเธเธญเธญเธเนเธฅเธเนเนเธฅเธฐเนเธเนเธเน€เธ•เธทเธญเธเนเธเธเธเธธเธเธ—เธฑเธเธ—เธตเน€เธกเธทเนเธญเธกเธตเธเธฒเธฃเธญเธฑเธเน€เธ”เธ•
          </p>
        </div>
        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          <Link href="/login" className="inline-flex items-center justify-center rounded-full bg-primary-600 px-6 py-4 text-base font-semibold text-white shadow-lg shadow-primary-300 transition hover:bg-primary-700">
            เน€เธเนเธฒเธชเธนเนเธฃเธฐเธเธเน€เธเธทเนเธญเน€เธฃเธดเนเธกเธเธญเธเธฃเธ–
          </Link>
          <Link href="/register" className="inline-flex items-center justify-center rounded-full border border-primary-200 px-6 py-4 text-base font-semibold text-primary-600 transition hover:bg-primary-50">
            เธชเธกเธฑเธเธฃเนเธเนเธเธฒเธเธฃเธฐเธเธ
          </Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        {[
          {
            title: 'เธชเธฃเนเธฒเธเธเธณเธเธญเนเธ”เนเธฃเธงเธ”เน€เธฃเนเธง',
            description: 'เนเธเธเธเธญเธฃเนเธกเธญเธฑเธเธเธฃเธดเธขเธฐเธเนเธงเธขเธเธฃเธญเธเธเนเธญเธกเธนเธฅเน€เธ”เธดเธกเนเธฅเธฐเธฅเธ”เธเธฒเธฃเธเธดเธกเธเนเธเนเธณ เธเธฃเนเธญเธกเธ•เธฃเธงเธเธชเธญเธเธเธงเธฒเธกเธเธฃเนเธญเธกเธเธญเธเธฃเธ–เนเธ”เธขเธญเธฑเธ•เนเธเธกเธฑเธ•เธด',
          },
          {
            title: 'เธ•เธดเธ”เธ•เธฒเธกเธชเธ–เธฒเธเธฐเนเธเธเน€เธฃเธตเธขเธฅเนเธ—เธกเน',
            description: 'เธฃเธนเนเธ—เธฑเธเธ—เธตเน€เธกเธทเนเธญเธเธนเนเธเธฑเธ”เธเธฒเธฃเธญเธเธธเธกเธฑเธ•เธดเธซเธฃเธทเธญเธเธเธดเน€เธชเธ เธเธฃเนเธญเธกเธเธฃเธฐเธงเธฑเธ•เธดเธเธณเธเธญเธ—เธตเนเน€เธเนเธฒเธ–เธถเธเนเธ”เนเธ—เธธเธเธ—เธตเน',
          },
          {
            title: 'เธฃเธญเธเธฃเธฑเธเธเธฒเธฃเนเธเนเธเธฒเธเธญเธญเธเนเธฅเธเน',
            description: 'เธเธฑเธเธ—เธถเธเธเธณเธเธญเนเธงเนเธฅเนเธงเธเธซเธเนเธฒเนเธกเนเนเธกเนเธกเธตเธญเธดเธเน€เธ—เธญเธฃเนเน€เธเนเธ• เธฃเธฐเธเธเธเธฐเธชเนเธเนเธซเนเธญเธฑเธ•เนเธเธกเธฑเธ•เธดเน€เธกเธทเนเธญเธเธฅเธฑเธเธกเธฒเธญเธญเธเนเธฅเธเน',
          },
          {
            title: 'เธเธฅเธญเธ”เธ เธฑเธขเธชเธณเธซเธฃเธฑเธเธญเธเธเนเธเธฃ',
            description: 'เธเนเธญเธกเธนเธฅเธ—เธธเธเธเธณเธเธญเธ–เธนเธเน€เธเนเธฒเธฃเธซเธฑเธช เธเธฃเนเธญเธกเธฃเธฐเธเธเธชเธดเธ—เธเธดเนเธเธฒเธฃเนเธเนเธเธฒเธเธ•เธฒเธกเธเธ—เธเธฒเธ—เนเธฅเธฐเธเธฑเธเธ—เธถเธเธเธฒเธฃเน€เธเธฅเธตเนเธขเธเนเธเธฅเธ',
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
              เธเธฃเนเธญเธกเนเธเนเธเธฒเธ
            </span>
            <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">เธขเธดเธเธ”เธตเธ•เนเธญเธเธฃเธฑเธเธเธฅเธฑเธ {user?.fullName}</h1>
            <p className="text-sm font-medium text-primary-600">
              เธเธ—เธเธฒเธ—เธเธญเธเธเธธเธ“: <span className="font-semibold text-primary-700">{user?.role}</span>
            </p>
            <p className="text-base leading-relaxed text-slate-600">
              เธ•เธดเธ”เธ•เธฒเธกเธเธณเธเธญเธ—เธตเนเธฃเธญเธ”เธณเน€เธเธดเธเธเธฒเธฃ เธ•เธฃเธงเธเธชเธญเธเธ•เธฒเธฃเธฒเธเธเธฒเธฃเนเธเนเธฃเธ–เธฅเนเธงเธเธซเธเนเธฒ เนเธฅเธฐเธฃเธฑเธเธเธฒเธฃเนเธเนเธเน€เธ•เธทเธญเธเธญเธฑเธ•เนเธเธกเธฑเธ•เธดเนเธกเนเธญเธญเธเนเธฅเธเน
            </p>
          </div>
          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            <Link href="/bookings/new" className="flex flex-col items-center gap-2 rounded-2xl bg-primary-600 px-4 py-5 text-center text-sm font-semibold text-white shadow-lg shadow-primary-300 transition hover:bg-primary-700">
              <span className="text-lg">โ•</span>
              เธชเธฃเนเธฒเธเธเธณเธเธญเนเธซเธกเน
            </Link>
            <Link href="/calendar" className="flex flex-col items-center gap-2 rounded-2xl border border-primary-200 bg-primary-50 px-4 py-5 text-center text-sm font-semibold text-primary-600 transition hover:bg-primary-100">
              <span className="text-lg">๐“…</span>
              เธเธเธดเธ—เธดเธเธเธฒเธฃเนเธเนเธฃเธ–
            </Link>
            <Link href="/profile" className="flex flex-col items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-5 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
              <span className="text-lg">๐‘ค</span>
              เธเธฑเธ”เธเธฒเธฃเนเธเธฃเนเธเธฅเน
            </Link>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm sm:p-8">
          <h2 className="text-lg font-semibold text-slate-900">เธชเธดเนเธเธ—เธตเนเธ•เนเธญเธเธ—เธณเธ•เนเธญเนเธ</h2>
          <ul className="mt-4 space-y-4 text-sm text-slate-600">
            <li className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">เธ•เธฃเธงเธเธชเธญเธเธเธณเธเธญเธ—เธตเนเธฃเธญเธญเธเธธเธกเธฑเธ•เธดเธเธฒเธเธ—เธตเธกเธเธฒเธ</li>
            <li className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">เธเธฑเธเธ—เธถเธเนเธเธเธเธฒเธฃเนเธเนเธฃเธ–เธชเธณเธซเธฃเธฑเธเธชเธฑเธเธ”เธฒเธซเนเธซเธเนเธฒ</li>
            <li className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">เธญเธฑเธเน€เธ”เธ•เธเนเธญเธกเธนเธฅเนเธเธฃเนเธเธฅเนเธชเธณเธซเธฃเธฑเธเธเธฒเธฃเธ•เธดเธ”เธ•เนเธญเธเธธเธเน€เธเธดเธ</li>
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
      {isAuthenticated ? (
        <main className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 px-4 py-8 sm:px-6 sm:py-10">
          <div className="mx-auto w-full max-w-5xl">{authenticatedContent}</div>
        </main>
      ) : (
        <AppShell isAuthenticated={false}>{guestContent}</AppShell>
      )}

      <MobileNotificationDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <NotificationCenter controller={notificationController} />
      </MobileNotificationDrawer>
    </>
  );
}

=======
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
>>>>>>> bc57f41 (Initial CAR-BOOKING project)
