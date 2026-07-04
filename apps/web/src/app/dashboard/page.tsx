'use client';

import { useRouter } from 'next/navigation';
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from '@visionops/ui';
import { AuthGuard } from '@/components/auth-guard';
import { authApi } from '@/features/auth/api';
import { useAuth } from '@/features/auth/use-auth';

const PLACEHOLDERS = [
  { title: 'Cameras', desc: 'Connect and monitor RTSP/ONVIF cameras.' },
  { title: 'Alerts', desc: 'Real-time alerts from your business rules.' },
  { title: 'Analytics', desc: 'Footfall, heatmaps, and operations trends.' },
  { title: 'Reports', desc: 'AI-generated daily, weekly, and monthly reports.' },
];

function Dashboard() {
  const router = useRouter();
  const { user, refreshToken, clear } = useAuth();

  const logout = async () => {
    if (refreshToken) await authApi.logout(refreshToken).catch(() => undefined);
    clear();
    router.replace('/login');
  };

  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between border-b px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold tracking-tight">
            VisionOps<span className="text-muted-foreground"> AI</span>
          </span>
          {user?.organization && (
            <span className="rounded-full border px-2.5 py-0.5 text-xs text-muted-foreground">
              {user.organization.name}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">{user?.user.full_name}</span>
          <Button variant="outline" size="sm" onClick={logout}>
            Log out
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold tracking-tight">
          Welcome back, {user?.user.full_name?.split(' ')[0]}.
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your workspace is ready. Modules below activate as they ship.
        </p>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {PLACEHOLDERS.map((item) => (
            <Card key={item.title}>
              <CardHeader>
                <CardTitle className="text-base">{item.title}</CardTitle>
                <CardDescription>{item.desc}</CardDescription>
              </CardHeader>
              <CardContent>
                <span className="text-xs text-muted-foreground">Coming soon</span>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <Dashboard />
    </AuthGuard>
  );
}
