'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  BarChart3,
  Bell,
  Camera,
  FileText,
  LayoutDashboard,
  Radio,
  Settings,
  SlidersHorizontal,
  Store,
} from 'lucide-react';
import { cn } from '@visionops/utils';
import { Button } from '@visionops/ui';
import { authApi } from '@/features/auth/api';
import { useAuth } from '@/features/auth/use-auth';
import { ConnectionStatus } from '@/components/connection-status';

const NAV = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard, enabled: true },
  { href: '/stores', label: 'Stores', icon: Store, enabled: true },
  { href: '/cameras', label: 'Cameras', icon: Camera, enabled: true },
  { href: '/live', label: 'Live view', icon: Radio, enabled: true },
  { href: '/rules', label: 'Rules', icon: SlidersHorizontal, enabled: true },
  { href: '/alerts', label: 'Alerts', icon: Bell, enabled: true },
  { href: '/events', label: 'Events', icon: FileText, enabled: true },
  { href: '/settings', label: 'Settings', icon: Settings, enabled: true },
] as const;

const SOON = [
  { label: 'Analytics', icon: BarChart3 },
  { label: 'Reports', icon: FileText },
] as const;

export function DashboardSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, refreshToken, clear } = useAuth();

  const logout = async () => {
    if (refreshToken) await authApi.logout(refreshToken).catch(() => undefined);
    clear();
    router.replace('/login');
  };

  return (
    <aside className="flex h-screen w-60 flex-col border-r bg-background">
      <div className="flex items-center gap-2 px-5 py-5">
        <span className="text-lg font-bold tracking-tight">
          VisionOps<span className="text-muted-foreground"> AI</span>
        </span>
      </div>

      {user?.organization && (
        <div className="mx-3 mb-2 flex items-center gap-2 rounded-md border px-3 py-2">
          {user.organization.logo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={user.organization.logo_url}
              alt=""
              className="h-6 w-6 rounded object-cover"
            />
          ) : (
            <span className="flex h-6 w-6 items-center justify-center rounded bg-primary text-xs font-semibold text-primary-foreground">
              {user.organization.name.charAt(0).toUpperCase()}
            </span>
          )}
          <span className="truncate text-sm font-medium">{user.organization.name}</span>
        </div>
      )}

      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors',
                active
                  ? 'bg-accent font-medium text-accent-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}

        <div className="px-3 pb-1 pt-4 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Coming soon
        </div>
        {SOON.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.label}
              className="flex cursor-not-allowed items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground/50"
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </div>
          );
        })}
      </nav>

      <div className="border-t p-3">
        <div className="mb-2 flex items-center justify-between px-2">
          <div className="min-w-0 text-sm">
            <p className="truncate font-medium">{user?.user.full_name}</p>
            <p className="truncate text-xs text-muted-foreground">{user?.user.email}</p>
          </div>
        </div>
        <div className="mb-2">
          <ConnectionStatus />
        </div>
        <Button variant="outline" size="sm" className="w-full" onClick={logout}>
          Log out
        </Button>
      </div>
    </aside>
  );
}
