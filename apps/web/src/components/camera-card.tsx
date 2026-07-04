'use client';

import Link from 'next/link';
import { Camera as CameraIcon } from 'lucide-react';
import { Card } from '@visionops/ui';
import { formatDateTime } from '@visionops/utils';
import { CameraStatusBadge } from '@/features/cameras/status';
import type { Camera } from '@/features/cameras/types';

export function CameraCard({ camera }: { camera: Camera }) {
  return (
    <Link href={`/cameras/${camera.id}`}>
      <Card className="overflow-hidden transition-colors hover:border-foreground/20">
        <div className="flex aspect-video items-center justify-center bg-muted">
          {camera.thumbnail_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={camera.thumbnail_url} alt="" className="h-full w-full object-cover" />
          ) : (
            <CameraIcon className="h-8 w-8 text-muted-foreground/40" />
          )}
        </div>
        <div className="flex items-center justify-between p-4">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{camera.name}</p>
            <p className="text-xs text-muted-foreground">
              {camera.last_seen_at
                ? `Seen ${formatDateTime(camera.last_seen_at)}`
                : 'Never connected'}
            </p>
          </div>
          <CameraStatusBadge status={camera.status} />
        </div>
      </Card>
    </Link>
  );
}
