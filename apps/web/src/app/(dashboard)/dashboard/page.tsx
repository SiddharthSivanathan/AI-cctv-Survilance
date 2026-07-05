'use client';

import Link from 'next/link';
import { useState } from 'react';
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Skeleton,
} from '@visionops/ui';
import { formatDateTime } from '@visionops/utils';
import { LineChart } from '@/components/charts/line-chart';
import { DonutChart } from '@/components/charts/donut-chart';
import { BarList } from '@/components/charts/bar-list';
import { useAuth } from '@/features/auth/use-auth';
import {
  useAlertBreakdown,
  useCameraHealth,
  useOverview,
  useTimeseries,
} from '@/features/analytics/hooks';
import { TIME_RANGES, type TimeRange } from '@/features/analytics/types';
import { useEvents } from '@/features/events/hooks';
import { eventLabel } from '@/features/events/types';
import { SeverityBadge } from '@/features/events/severity';

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#6b7280',
};

function Kpi({ label, value, href }: { label: string; value: string | number; href?: string }) {
  const body = (
    <Card className={href ? 'transition-colors hover:border-foreground/20' : ''}>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-3xl">{value}</CardTitle>
      </CardHeader>
    </Card>
  );
  return href ? <Link href={href}>{body}</Link> : body;
}

export default function DashboardOverviewPage() {
  const { user } = useAuth();
  const [range, setRange] = useState<TimeRange>('today');

  const overview = useOverview();
  const series = useTimeseries(range);
  const breakdown = useAlertBreakdown(range);
  const health = useCameraHealth();
  const activity = useEvents();

  const points = series.data?.points ?? [];
  const footfall = points.map((p) => ({ label: p.bucket, value: p.footfall }));
  const occupancy = points.map((p) => ({ label: p.bucket, value: p.occupancy_peak }));
  const queue = points.map((p) => ({ label: p.bucket, value: p.queue_peak }));

  const o = overview.data;

  return (
    <div className="mx-auto max-w-6xl px-8 py-10">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome back, {user?.user.full_name?.split(' ')[0]}.
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">Live operations overview.</p>
        </div>
        <div className="flex gap-1 rounded-md border p-1">
          {TIME_RANGES.map((r) => (
            <Button
              key={r.value}
              size="sm"
              variant={range === r.value ? 'default' : 'ghost'}
              onClick={() => setRange(r.value)}
            >
              {r.label}
            </Button>
          ))}
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Kpi label="Active cameras" value={o?.active_cameras ?? '—'} href="/cameras" />
        <Kpi label="Cameras online" value={o?.cameras_online ?? '—'} href="/cameras" />
        <Kpi label="Alerts today" value={o?.alerts_today ?? '—'} href="/alerts" />
        <Kpi label="Critical alerts" value={o?.critical_alerts_today ?? '—'} href="/alerts" />
        <Kpi label="Current occupancy" value={o?.current_occupancy ?? '—'} />
        <Kpi label="Today’s footfall" value={o?.todays_footfall ?? '—'} />
      </div>

      {/* Charts */}
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Footfall trend</CardTitle>
          </CardHeader>
          <CardContent>
            {series.isLoading ? <Skeleton className="h-40" /> : <LineChart data={footfall} />}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Peak occupancy</CardTitle>
          </CardHeader>
          <CardContent>
            {series.isLoading ? (
              <Skeleton className="h-40" />
            ) : (
              <LineChart data={occupancy} color="#8b5cf6" />
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Peak queue length</CardTitle>
          </CardHeader>
          <CardContent>
            {series.isLoading ? <Skeleton className="h-40" /> : <LineChart data={queue} color="#f97316" />}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Camera health</CardTitle>
          </CardHeader>
          <CardContent>
            {health.isLoading || !health.data ? (
              <Skeleton className="h-36" />
            ) : (
              <DonutChart
                segments={[
                  { label: 'Online', value: health.data.online, color: '#22c55e' },
                  { label: 'Offline', value: health.data.offline, color: '#ef4444' },
                ]}
              />
            )}
            {health.data && (
              <p className="mt-3 text-sm text-muted-foreground">
                Uptime: <span className="font-medium text-foreground">{health.data.uptime_pct}%</span>
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Alert breakdown + activity */}
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Alerts by severity</CardTitle>
          </CardHeader>
          <CardContent>
            <BarList
              data={Object.entries(breakdown.data?.by_severity ?? {}).map(([label, value]) => ({
                label,
                value,
                color: SEVERITY_COLORS[label] ?? undefined,
              }))}
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Alerts by type</CardTitle>
          </CardHeader>
          <CardContent>
            <BarList
              data={Object.entries(breakdown.data?.by_type ?? {}).map(([label, value]) => ({
                label: eventLabel(label),
                value,
              }))}
            />
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-base">Recent activity</CardTitle>
          <Link href="/events" className="text-sm text-muted-foreground hover:underline">
            View all →
          </Link>
        </CardHeader>
        <CardContent>
          {activity.isLoading && <Skeleton className="h-24" />}
          {!activity.isLoading && (activity.data?.length ?? 0) === 0 && (
            <p className="py-6 text-center text-sm text-muted-foreground">No recent activity.</p>
          )}
          <div className="divide-y">
            {activity.data?.slice(0, 8).map((event) => (
              <div key={event.id} className="flex items-center justify-between py-2.5">
                <div className="flex items-center gap-3">
                  <SeverityBadge severity={event.severity} />
                  <span className="text-sm font-medium">{eventLabel(event.event_type)}</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {formatDateTime(event.started_at)}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
