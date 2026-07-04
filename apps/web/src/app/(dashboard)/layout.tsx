'use client';

import { AuthGuard } from '@/components/auth-guard';
import { DashboardSidebar } from '@/components/dashboard-sidebar';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen">
        <DashboardSidebar />
        <div className="flex-1 overflow-y-auto">{children}</div>
      </div>
    </AuthGuard>
  );
}
