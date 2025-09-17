import type { ReactNode } from 'react';
import Link from 'next/link';
import { ShieldCheck, Users, Bell } from 'lucide-react';

interface HighlightItem {
  title: string;
  description: string;
  icon: ReactNode;
}

interface AuthLayoutProps {
  heading: string;
  subheading: string;
  description?: string;
  highlights?: HighlightItem[];
  children: ReactNode;
  footer?: ReactNode;
}

const defaultHighlights: HighlightItem[] = [
  {
    title: 'การอนุมัติหลายระดับ',
    description: 'รองรับการอนุมัติจากหัวหน้างาน ผู้จัดการ และผู้ดูแลระบบในระบบเดียว',
    icon: <ShieldCheck className="h-6 w-6 text-primary-500" aria-hidden="true" />,
  },
  {
    title: 'จัดการผู้ใช้งานง่าย',
    description: 'กำหนดบทบาทและสิทธิ์การเข้าถึงได้อย่างยืดหยุ่นตามโครงสร้างองค์กร',
    icon: <Users className="h-6 w-6 text-primary-500" aria-hidden="true" />,
  },
  {
    title: 'แจ้งเตือนทันที',
    description: 'รับการแจ้งเตือนผ่านอีเมล WebSocket และ Mobile App เพื่อไม่ให้พลาดทุกการอนุมัติ',
    icon: <Bell className="h-6 w-6 text-primary-500" aria-hidden="true" />,
  },
];

export function AuthLayout({
  heading,
  subheading,
  description,
  highlights = defaultHighlights,
  children,
  footer,
}: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-100">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center px-4 py-12 lg:flex-row lg:items-center lg:gap-16">
        <section className="max-w-xl text-center lg:text-left">
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-full bg-primary-100 px-4 py-1 text-xs font-semibold uppercase tracking-wider text-primary-700"
          >
            Office Vehicle Booking
          </Link>
          <h1 className="mt-6 text-4xl font-bold text-gray-900 sm:text-5xl">{heading}</h1>
          <p className="mt-4 text-lg text-gray-600">{subheading}</p>
          {description ? <p className="mt-3 text-sm text-gray-500">{description}</p> : null}

          <dl className="mt-10 grid gap-6 sm:grid-cols-2">
            {highlights.map((item) => (
              <div key={item.title} className="rounded-2xl bg-white/70 p-5 text-left shadow-sm ring-1 ring-gray-100 backdrop-blur">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-50">
                    {item.icon}
                  </div>
                  <div>
                    <dt className="text-base font-semibold text-gray-900">{item.title}</dt>
                    <dd className="mt-1 text-sm text-gray-600">{item.description}</dd>
                  </div>
                </div>
              </div>
            ))}
          </dl>
        </section>

        <section className="mt-12 w-full max-w-md lg:mt-0">
          <div className="card relative overflow-hidden">
            <div className="absolute inset-x-6 top-0 h-1 rounded-b-full bg-gradient-to-r from-primary-400 via-secondary-400 to-primary-500" />
            <div className="mt-6">{children}</div>
          </div>
          {footer ? <div className="mt-6 text-center text-sm text-gray-600">{footer}</div> : null}
        </section>
      </div>
    </div>
  );
}
