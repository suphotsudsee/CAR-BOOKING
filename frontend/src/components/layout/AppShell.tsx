'use client';

import { BellRing, Home, LogIn, Menu, User } from 'lucide-react';
import Link from 'next/link';
import { useMemo, useState } from 'react';

import { useOnlineStatus } from '@/hooks/useOnlineStatus';

interface AppShellProps {
  isAuthenticated: boolean;
  fullName?: string;
  unreadCount?: number;
  onOpenNotifications?: () => void;
  onLogout?: () => void;
  children: React.ReactNode;
}

export function AppShell({
  isAuthenticated,
  fullName,
  unreadCount = 0,
  onOpenNotifications,
  onLogout,
  children,
}: AppShellProps) {
  const isOnline = useOnlineStatus();
  const [menuOpen, setMenuOpen] = useState(false);

  const firstName = useMemo(() => fullName?.split(' ')[0] ?? '', [fullName]);

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-primary-50 via-white to-secondary-50">
      <header className="sticky top-0 z-20 border-b border-white/50 bg-white/80 backdrop-blur">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-primary-100 bg-white text-primary-600 shadow-sm sm:hidden"
              onClick={() => setMenuOpen((value) => !value)}
            >
              <Menu className="h-5 w-5" />
              <span className="sr-only">เปิดเมนู</span>
            </button>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-primary-500">Office Vehicle</p>
              <p className="text-lg font-bold text-slate-900">Booking System</p>
              {isAuthenticated && firstName && (
                <p className="text-xs text-slate-500">ยินดีต้อนรับกลับ {firstName}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <button
                type="button"
                onClick={onOpenNotifications}
                className="relative inline-flex h-11 w-11 items-center justify-center rounded-full border border-primary-100 bg-white text-primary-600 shadow"
              >
                <BellRing className="h-5 w-5" />
                {unreadCount > 0 && (
                  <span className="absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
                    {unreadCount}
                  </span>
                )}
                <span className="sr-only">เปิดการแจ้งเตือน</span>
              </button>
            ) : (
              <Link
                href="/login"
                className="inline-flex h-11 items-center gap-2 rounded-full border border-primary-100 bg-white px-4 text-sm font-semibold text-primary-600 shadow"
              >
                <LogIn className="h-4 w-4" />
                เข้าสู่ระบบ
              </Link>
            )}

            {isAuthenticated && (
              <button
                type="button"
                onClick={onLogout}
                className="hidden rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 sm:inline-flex"
              >
                ออกจากระบบ
              </button>
            )}
          </div>
        </div>

        {menuOpen && (
          <nav className="border-t border-primary-100 bg-white/95 px-4 py-3 sm:hidden">
            <ul className="flex flex-col gap-2 text-sm text-slate-600">
              <li>
                <Link href="/" className="inline-flex w-full items-center gap-3 rounded-xl bg-primary-50 px-4 py-3 font-semibold text-primary-600">
                  <Home className="h-4 w-4" /> หน้าหลัก
                </Link>
              </li>
              {isAuthenticated ? (
                <>
                  <li>
                    <button
                      type="button"
                      className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left"
                      onClick={() => {
                        onOpenNotifications?.();
                        setMenuOpen(false);
                      }}
                    >
                      <BellRing className="h-4 w-4" /> การแจ้งเตือน ({unreadCount})
                    </button>
                  </li>
                  <li>
                    <Link href="/profile" className="flex w-full items-center gap-3 rounded-xl px-4 py-3">
                      <User className="h-4 w-4" /> โปรไฟล์ของฉัน
                    </Link>
                  </li>
                  <li>
                    <button
                      type="button"
                      className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left"
                      onClick={() => {
                        setMenuOpen(false);
                        onLogout?.();
                      }}
                    >
                      <LogIn className="h-4 w-4 rotate-180" /> ออกจากระบบ
                    </button>
                  </li>
                </>
              ) : (
                <li>
                  <Link href="/register" className="flex w-full items-center gap-3 rounded-xl px-4 py-3">
                    <User className="h-4 w-4" /> สมัครใช้งานระบบ
                  </Link>
                </li>
              )}
            </ul>
          </nav>
        )}

        {!isOnline && (
          <div className="border-t border-amber-200 bg-amber-50 px-4 py-2 text-xs font-medium text-amber-700">
            โหมดออฟไลน์: ข้อมูลจะซิงค์ให้อัตโนมัติเมื่อกลับมาเชื่อมต่ออินเทอร์เน็ต
          </div>
        )}
      </header>

      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 pb-24 pt-8 sm:pb-12 sm:pt-12">
        {children}
      </main>

      <footer className="fixed bottom-0 left-0 right-0 z-30 border-t border-white/60 bg-white/95 px-4 py-2 shadow-[0_-4px_30px_rgba(15,23,42,0.08)] backdrop-blur md:hidden">
        <nav className="mx-auto flex w-full max-w-3xl items-center justify-between">
          <Link href="/" className="flex flex-1 flex-col items-center gap-1 rounded-full px-3 py-2 text-xs font-semibold text-primary-600">
            <Home className="h-5 w-5" /> หน้าหลัก
          </Link>
          {isAuthenticated ? (
            <>
              <button
                type="button"
                className="flex flex-1 flex-col items-center gap-1 rounded-full px-3 py-2 text-xs font-semibold text-slate-600"
                onClick={onOpenNotifications}
              >
                <div className="relative">
                  <BellRing className="h-5 w-5" />
                  {unreadCount > 0 && (
                    <span className="absolute -right-1 -top-1 inline-flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
                      {unreadCount}
                    </span>
                  )}
                </div>
                แจ้งเตือน
              </button>
              <Link
                href="/profile"
                className="flex flex-1 flex-col items-center gap-1 rounded-full px-3 py-2 text-xs font-semibold text-slate-600"
              >
                <User className="h-5 w-5" /> โปรไฟล์
              </Link>
            </>
          ) : (
            <Link
              href="/register"
              className="flex flex-1 flex-col items-center gap-1 rounded-full px-3 py-2 text-xs font-semibold text-slate-600"
            >
              <User className="h-5 w-5" /> สมัคร
            </Link>
          )}
        </nav>
      </footer>
    </div>
  );
}
