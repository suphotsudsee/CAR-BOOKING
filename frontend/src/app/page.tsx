"use client";

import { FormEvent, useState } from 'react';

import { NotificationCenter } from '../components/notifications/NotificationCenter';

export default function HomePage() {
  const [tokenInput, setTokenInput] = useState('');
  const [activeToken, setActiveToken] = useState<string | null>(null);

  const handleConnect = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setActiveToken(tokenInput.trim() || null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50">
      <div className="container mx-auto px-4 py-16">
        <div className="grid gap-8 lg:grid-cols-[2fr_3fr]">
          <div className="space-y-6">
            <div className="rounded-2xl bg-white p-8 shadow-lg">
              <h1 className="text-4xl font-bold text-gray-900">
                ระบบจองรถสำนักงาน
              </h1>
              <p className="mt-3 text-xl text-gray-600">
                Office Vehicle Booking System
              </p>
              <p className="mt-4 text-sm text-gray-500">
                แพลตฟอร์มบริหารจัดการการขอใช้รถสำหรับองค์กร พร้อมระบบอนุมัติหลายขั้นตอน
                การติดตามสถานะ และการแจ้งเตือนหลากหลายช่องทาง
              </p>

              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <button className="btn-primary py-3">เข้าสู่ระบบ</button>
                <button className="btn-secondary py-3">ดูคู่มือการใช้งาน</button>
              </div>
            </div>

            <form
              onSubmit={handleConnect}
              className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
            >
              <h2 className="text-xl font-semibold text-gray-900">
                เชื่อมต่อศูนย์แจ้งเตือนแบบเรียลไทม์
              </h2>
              <p className="mt-2 text-sm text-gray-500">
                วาง JWT Access Token ของคุณเพื่อรับการแจ้งเตือนแบบทันทีผ่าน WebSocket
              </p>
              <div className="mt-4 space-y-3">
                <input
                  type="text"
                  value={tokenInput}
                  onChange={(event) => setTokenInput(event.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-200"
                  placeholder="ใส่ Access Token"
                />
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="submit"
                    className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-600"
                  >
                    เชื่อมต่อศูนย์แจ้งเตือน
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveToken(null)}
                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
                  >
                    ยกเลิกการเชื่อมต่อ
                  </button>
                  {activeToken ? (
                    <span className="text-sm text-green-600">เชื่อมต่อเรียบร้อย</span>
                  ) : (
                    <span className="text-sm text-gray-400">ยังไม่ได้เชื่อมต่อ</span>
                  )}
                </div>
              </div>
            </form>
          </div>

          <NotificationCenter authToken={activeToken} />
        </div>
      </div>
    </div>
  );
}