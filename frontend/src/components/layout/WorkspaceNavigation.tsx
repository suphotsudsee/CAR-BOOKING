Exit code: 0
Wall time: 0.6 seconds
Output:
'use client';

import {
  Archive,
  BarChart3,
  CalendarDays,
  ClipboardCheck,
  FilePlus2,
  Files,
  LayoutDashboard,
  LogOut,
  ShieldCheck,
  UserRound,
  type LucideIcon,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useMemo } from 'react';

import { USER_ROLES, type UserRole, useAuth } from '@/context/AuthContext';

interface WorkspaceTab {
  href: string;
  label: string;
  group: string;
  icon: LucideIcon;
  roles?: UserRole[];
}

const workspaceTabs: WorkspaceTab[] = [
  { href: '/', label: 'เธซเธเนเธฒเธซเธฅเธฑเธ', group: 'เธ เธฒเธเธฃเธงเธก', icon: Archive },
  { href: '/dashboard', label: 'เนเธ”เธเธเธญเธฃเนเธ”', group: 'เธ เธฒเธเธฃเธงเธก', icon: LayoutDashboard },
  {
    href: '/bookings/new',
    label: 'เธชเธฃเนเธฒเธเธเธณเธเธญ',
    group: 'เธเธฒเธเธเธญเธเธฃเธ–',
    icon: FilePlus2,
    roles: [USER_ROLES.REQUESTER, USER_ROLES.MANAGER, USER_ROLES.FLEET_ADMIN],
  },
  { href: '/bookings', label: 'เธฃเธฒเธขเธเธฒเธฃเธเธญเธ', group: 'เธเธฒเธเธเธญเธเธฃเธ–', icon: Files },
  {
    href: '/bookings/approvals',
    label: 'เธเธฒเธเธญเธเธธเธกเธฑเธ•เธด',
    group: 'เธเธฒเธเธเธญเธเธฃเธ–',
    icon: ClipboardCheck,
    roles: [USER_ROLES.MANAGER, USER_ROLES.FLEET_ADMIN],
  },
  { href: '/calendar', label: 'เธเธเธดเธ—เธดเธเธฃเธ–', group: 'เธ•เธฒเธฃเธฒเธเธเธฒเธ', icon: CalendarDays },
  {
    href: '/reports',
    label: 'เธฃเธฒเธขเธเธฒเธ',
    group: 'เธเนเธญเธกเธนเธฅ',
    icon: BarChart3,
    roles: [USER_ROLES.MANAGER, USER_ROLES.FLEET_ADMIN, USER_ROLES.AUDITOR],
  },
  {
    href: '/admin/2fa',
    label: 'เธเธงเธฒเธกเธเธฅเธญเธ”เธ เธฑเธข',
    group: 'เธ•เธฑเนเธเธเนเธฒเธฃเธฐเธเธ',
    icon: ShieldCheck,
    roles: [USER_ROLES.MANAGER, USER_ROLES.FLEET_ADMIN],
  },
  { href: '/profile', label: 'เนเธเธฃเนเธเธฅเน', group: 'เธเธฑเธเธเธตเธเธญเธเธเธฑเธ', icon: UserRound },
];

function matchesPath(pathname: string, href: string) {
  if (href === '/') {
    return pathname === '/';
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function WorkspaceNavigation() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, initializing, logout } = useAuth();

  const visibleTabs = useMemo(
    () => workspaceTabs.filter((tab) => !tab.roles || (user ? tab.roles.includes(user.role) : false)),
    [user],
  );

  const activeHref = useMemo(
    () =>
      visibleTabs
        .filter((tab) => matchesPath(pathname, tab.href))
        .sort((left, right) => right.href.length - left.href.length)[0]?.href,
    [pathname, visibleTabs],
  );

  if (initializing || !isAuthenticated || !user) {
    return null;
  }

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <header className="sticky top-0 z-40 border-b border-slate-300 bg-[#f5f1e8]/95 shadow-sm backdrop-blur">
      <div className="mx-auto w-full max-w-7xl px-3 pt-3 sm:px-6 lg:px-8">
        <div className="mb-3 flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-slate-900">
              <Archive className="h-5 w-5 shrink-0 text-amber-700" aria-hidden="true" />
              <p className="truncate text-base font-bold sm:text-lg">เธ•เธนเนเน€เธญเธเธชเธฒเธฃเธเธฒเธเธฃเธ–</p>
            </div>
            <p className="mt-0.5 truncate text-xs text-slate-500">
              เน€เธฅเธทเธญเธเนเธเนเธกเธเธฒเธเธ—เธตเนเธ•เนเธญเธเธเธฒเธฃเน€เธเธดเธ” โ€ข {user.fullName}
            </p>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            className="inline-flex shrink-0 items-center gap-2 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-600 shadow-sm transition hover:border-red-200 hover:bg-red-50 hover:text-red-700 sm:text-sm"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
            <span className="hidden sm:inline">เธญเธญเธเธเธฒเธเธฃเธฐเธเธ</span>
          </button>
        </div>

        <nav aria-label="เนเธเนเธกเธเธฒเธเธ—เธฑเนเธเธซเธกเธ”">
          <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3 md:grid-cols-5 xl:grid-cols-9">
            {visibleTabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeHref === tab.href;

              return (
                <Link
                  key={tab.href}
                  href={tab.href}
                  aria-current={isActive ? 'page' : undefined}
                  className={`group relative flex min-h-[68px] min-w-0 items-center gap-2 rounded-t-xl border px-3 py-2 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 ${
                    isActive
                      ? '-mb-px border-amber-300 border-b-white bg-white text-primary-700 shadow-[0_-3px_12px_rgba(15,23,42,0.06)]'
                      : 'border-slate-300 bg-[#e8dfcd] text-slate-700 hover:-translate-y-0.5 hover:border-amber-300 hover:bg-[#f0e8d8]'
                  }`}
                >
                  <span
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
                      isActive ? 'bg-primary-100 text-primary-700' : 'bg-white/70 text-amber-800'
                    }`}
                  >
                    <Icon className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-[10px] font-medium text-slate-500">{tab.group}</span>
                    <span className="block truncate text-xs font-bold sm:text-sm">{tab.label}</span>
                  </span>
                  {isActive ? <span className="absolute inset-x-3 top-0 h-1 rounded-b-full bg-primary-500" /> : null}
                </Link>
              );
            })}
          </div>
          <div className="h-2 rounded-b-xl border-x border-b border-slate-400 bg-gradient-to-b from-slate-300 to-slate-400 shadow-inner" />
        </nav>
      </div>
    </header>
  );
}


