'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
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
import { BarList } from '@/components/charts/bar-list';
import { reportsApi } from '@/features/reports/api';
import { useReport } from '@/features/reports/hooks';
import { eventLabel } from '@/features/events/types';
import { SeverityBadge, StatusBadge } from '@/features/events/severity';

function Kpi({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardHeader>
    </Card>
  );
}

export default function ReportViewPage() {
  const params = useParams<{ id: string }>();
  const { data: report, isLoading, isError } = useReport(params.id);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-8 py-10">
        <Skeleton className="h-96" />
      </div>
    );
  }
  if (isError || !report) {
    return (
      <div className="mx-auto max-w-4xl px-8 py-10">
        <p className="text-sm text-destructive">Report not found.</p>
        <Link href="/reports" className="text-sm hover:underline">
          ← Back to reports
        </Link>
      </div>
    );
  }

  const d = report.data;

  return (
    <div className="mx-auto max-w-4xl px-8 py-10">
      <Link href="/reports" className="text-sm text-muted-foreground hover:underline">
        ← Back to reports
      </Link>

      <div className="mt-4 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold capitalize tracking-tight">
            {d.report_type} report
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {d.company_name} · {d.start_date} → {d.end_date} · generated{' '}
            {formatDateTime(d.generated_at)}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => reportsApi.download(report.id, 'pdf')}>
            PDF
          </Button>
          <Button variant="outline" size="sm" onClick={() => reportsApi.download(report.id, 'csv')}>
            CSV
          </Button>
        </div>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Executive summary</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-1.5 text-sm">
            {d.executive_summary.map((b, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-muted-foreground">•</span>
                {b}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi label="Total footfall" value={d.total_footfall} />
        <Kpi label="Peak occupancy" value={d.peak_occupancy} />
        <Kpi label="Total alerts" value={d.total_alerts} />
        <Kpi label="Uptime" value={`${d.overall_uptime_pct}%`} />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Footfall trend</CardTitle>
          </CardHeader>
          <CardContent>
            <LineChart data={d.footfall_trend.map((p) => ({ label: p.label, value: p.value }))} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Alerts by type</CardTitle>
          </CardHeader>
          <CardContent>
            <BarList
              data={Object.entries(d.alert_summary.by_type).map(([label, value]) => ({
                label: eventLabel(label),
                value,
              }))}
            />
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Cameras</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="divide-y text-sm">
            {d.cameras.map((c) => (
              <div key={c.camera_id} className="flex items-center justify-between py-2">
                <span className="font-medium">{c.camera_name}</span>
                <span className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>Footfall {c.total_footfall}</span>
                  <span>Alerts {c.total_events}</span>
                  <StatusBadge status={c.status === 'online' ? 'resolved' : 'open'} />
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Recent alerts</CardTitle>
        </CardHeader>
        <CardContent>
          {d.alert_rows.length === 0 ? (
            <p className="text-sm text-muted-foreground">No alerts in this period.</p>
          ) : (
            <div className="divide-y text-sm">
              {d.alert_rows.map((r, i) => (
                <div key={i} className="flex items-center justify-between py-2">
                  <div className="flex items-center gap-3">
                    <SeverityBadge severity={r.severity} />
                    <span>{eventLabel(r.event_type)}</span>
                    <span className="text-xs text-muted-foreground">{r.camera_name}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">{formatDateTime(r.time)}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-1.5 text-sm">
            {d.recommendations.map((r, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-muted-foreground">•</span>
                {r}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
