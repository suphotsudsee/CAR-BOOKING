import { ReactNode } from 'react';

export const metadata = {
  title: 'ระบบจัดการการจองรถ - Booking Management',
  description: 'ติดตาม จัดการ และสร้างคำขอจองรถบริการขององค์กร',
};

export default function BookingsLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 py-10">
      <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
        {children}
      </div>
    </div>
  );
}
