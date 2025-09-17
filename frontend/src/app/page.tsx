"use client";

import Link from 'next/link';
import { useRouter } from 'next/navigation';

import { NotificationCenter } from '@/components/notifications/NotificationCenter';
import { useAuth } from '@/context/AuthContext';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50">
        <div className="container mx-auto px-4 py-16">
          <div className="grid gap-8 lg:grid-cols-[2fr_3fr]">
            <div className="space-y-6">
              <div className="rounded-2xl bg-white p-8 shadow-lg">
                <h1 className="text-4xl font-bold text-gray-900">ระบบจองรถสำนักงาน</h1>
                <p className="mt-3 text-xl text-gray-600">Office Vehicle Booking System</p>
                <p className="mt-4 text-sm text-gray-500">
                  แพลตฟอร์มบริหารจัดการการขอใช้รถสำหรับองค์กร พร้อมระบบอนุมัติหลายขั้นตอน การติดตามสถานะ และการแจ้งเตือนหลากหลายช่องทาง
                </p>

                <div className="mt-6 grid gap-3 sm:grid-cols-2">
                  <Link href="/login" className="btn-primary py-3 text-center">
                    เข้าสู่ระบบ
                  </Link>
                  <Link href="/register" className="btn-secondary py-3 text-center">
                    ลงทะเบียนใช้งาน
                  </Link>
                </div>
              </div>
            </div>

            <NotificationCenter />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50">
      <div className="container mx-auto px-4 py-16">
        <div className="grid gap-8 lg:grid-cols-[2fr_3fr]">
          <div className="space-y-6">
            <div className="rounded-2xl bg-white p-8 shadow-lg">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm uppercase tracking-wide text-primary-500">พร้อมใช้งาน</p>
                  <h1 className="mt-1 text-3xl font-bold text-gray-900">ยินดีต้อนรับกลับ {user?.fullName}</h1>
                  <p className="mt-2 text-sm text-gray-500">
                    บทบาทของคุณ: <span className="font-semibold text-gray-700">{user?.role}</span>
                  </p>
                </div>
                <div className="flex gap-3">
                  <Link href="/profile" className="btn-secondary whitespace-nowrap px-4 py-2">
                    จัดการโปรไฟล์
                  </Link>
                  <button type="button" onClick={handleLogout} className="btn-outline whitespace-nowrap px-4 py-2">
                    ออกจากระบบ
                  </button>
                </div>
              </div>
              <p className="mt-6 text-sm text-gray-600">
                ตรวจสอบการแจ้งเตือนล่าสุดและติดตามสถานะคำขอจองรถของคุณได้ทันที ระบบจะต่ออายุการเข้าสู่ระบบให้อัตโนมัติเมื่อโทเคนใกล้หมดอายุเพื่อให้คุณใช้งานได้อย่างต่อเนื่อง
              </p>
            </div>
          </div>

          <NotificationCenter />
        </div>
      </div>
    </div>
  );
}
