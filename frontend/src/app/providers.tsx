Exit code: 0
Wall time: 0.5 seconds
Output:
'use client';

import { useEffect } from 'react';

import { WorkspaceNavigation } from '@/components/layout/WorkspaceNavigation';
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
      <WorkspaceNavigation />
      {children}
    </AuthProvider>
  );
}

export default Providers;

