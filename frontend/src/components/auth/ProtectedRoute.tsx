'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import { useAuth, UserRole } from '@/context/AuthContext';

interface ProtectedRouteProps {
  roles?: UserRole[];
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export function ProtectedRoute({ roles, fallback, children }: ProtectedRouteProps) {
  const router = useRouter();
  const { isAuthenticated, initializing, user } = useAuth();

  useEffect(() => {
    if (initializing) {
      return;
    }

    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }

    if (roles && roles.length > 0 && user && !roles.includes(user.role)) {
      router.replace('/');
    }
  }, [initializing, isAuthenticated, roles, router, user]);

  if (initializing) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-sm text-gray-500">กำลังตรวจสอบสิทธิ์การเข้าใช้งาน...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return fallback ? <>{fallback}</> : null;
  }

  if (roles && roles.length > 0 && user && !roles.includes(user.role)) {
    return (
      fallback ?? (
        <div className="flex min-h-[60vh] items-center justify-center">
          <div className="rounded-lg border border-red-200 bg-red-50 px-6 py-4 text-sm text-red-700">
            คุณไม่มีสิทธิ์เข้าถึงหน้าดังกล่าว
          </div>
        </div>
      )
    );
  }

  return <>{children}</>;
}

export default ProtectedRoute;
