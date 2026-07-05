'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Button, Card, CardContent, Select, Skeleton } from '@visionops/ui';
import { formatDateTime } from '@visionops/utils';
import { useGenerateReport, useReports } from '@/features/reports/hooks';
import { REPORT_TYPES } from '@/features/reports/types';

export default function ReportsPage() {
  const router = useRouter();
  const { data: reports, isLoading } = useReports();
  const generate = useGenerateReport();
  const [type, setType] = useState('daily');

  const onGenerate = async () => {
    const report = await generate.mutateAsync(type);
    router.push(`/reports/${report.id}`);
  };

  return (
    <div className="mx-auto max-w-4xl px-8 py-10">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Reports</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Operational summaries — view, and export to PDF or CSV.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={type} onChange={(e) => setType(e.target.value)} className="w-32">
            {REPORT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </Select>
          <Button onClick={onGenerate} disabled={generate.isPending}>
            {generate.isPending ? 'Generating…' : 'Generate'}
          </Button>
        </div>
      </div>

      {isLoading && <Skeleton className="h-24" />}
      {!isLoading && reports?.length === 0 && (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No reports yet. Generate one above.
          </CardContent>
        </Card>
      )}
      {!isLoading && reports && reports.length > 0 && (
        <div className="space-y-2">
          {reports.map((r) => (
            <Link key={r.id} href={`/reports/${r.id}`}>
              <Card className="transition-colors hover:border-foreground/20">
                <CardContent className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium capitalize">{r.report_type} report</p>
                    <p className="text-xs text-muted-foreground">
                      {r.period_start} → {r.period_end}
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {formatDateTime(r.generated_at)}
                  </span>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
