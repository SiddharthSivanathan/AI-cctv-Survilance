'use client';

import { AuthGuard } from '@/components/auth-guard';
import { DashboardSidebar } from '@/components/dashboard-sidebar';
import { RealtimeProvider } from '@/features/realtime/socket-provider';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <RealtimeProvider>
        <div className="flex min-h-screen">
          <DashboardSidebar />
          <div className="flex-1 overflow-y-auto">{children}</div>
        </div>
      </RealtimeProvider>
    </AuthGuard>
  );
}
