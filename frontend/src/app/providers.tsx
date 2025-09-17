'use client';

import { useEffect } from 'react';

import { AuthProvider } from '@/context/AuthContext';
import { registerServiceWorker } from '@/lib/pwa/client';

function ServiceWorkerManager() {
  useEffect(() => {
    void registerServiceWorker();
  }, []);

  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <ServiceWorkerManager />
      {children}
    </AuthProvider>
  );
}

export default Providers;
