'use client';

import { useState } from 'react';
import { Button, Card, CardContent, Skeleton } from '@visionops/ui';
import { formatDateTime } from '@visionops/utils';
import { useAcknowledgeAlert, useAlerts } from '@/features/events/hooks';
import { eventLabel } from '@/features/events/types';
import { SeverityBadge, StatusBadge } from '@/features/events/severity';

const FILTERS = ['open', 'acknowledged', 'resolved'] as const;

export default function AlertsPage() {
  const [filter, setFilter] = useState<string | undefined>('open');
  const { data: alerts, isLoading } = useAlerts(filter);
  const acknowledge = useAcknowledgeAlert();

  return (
    <div className="mx-auto max-w-4xl px-8 py-10">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Alert Center</h1>
          <p className="mt-1 text-sm text-muted-foreground">Real-time alerts from your rules.</p>
        </div>
        <div className="flex gap-1 rounded-md border p-1">
          {FILTERS.map((f) => (
            <Button
              key={f}
              size="sm"
              variant={filter === f ? 'default' : 'ghost'}
              onClick={() => setFilter(f)}
            >
              {f}
            </Button>
          ))}
        </div>
      </div>

      {isLoading && <Skeleton className="h-24" />}
      {!isLoading && alerts?.length === 0 && (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No {filter} alerts.
          </CardContent>
        </Card>
      )}
      {!isLoading && alerts && alerts.length > 0 && (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <Card key={alert.id}>
              <CardContent className="flex items-center justify-between py-4">
                <div className="flex items-center gap-3">
                  <SeverityBadge severity={alert.severity} />
                  <div>
                    <p className="text-sm font-medium">{eventLabel(alert.event_type)}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDateTime(alert.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={alert.status} />
                  {!alert.acknowledged && alert.status !== 'resolved' && (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={acknowledge.isPending}
                      onClick={() => acknowledge.mutate(alert.id)}
                    >
                      Acknowledge
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
