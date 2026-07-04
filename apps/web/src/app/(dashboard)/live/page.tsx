'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button, Card, CardContent, Skeleton } from '@visionops/ui';
import { cn } from '@visionops/utils';
import { LivePlayer } from '@/components/live-player';
import { CameraStatusBadge } from '@/features/cameras/status';
import { useCameras } from '@/features/cameras/hooks';

const LAYOUTS = {
  '1': 'grid-cols-1',
  '4': 'grid-cols-1 sm:grid-cols-2',
  '9': 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
} as const;

type Layout = keyof typeof LAYOUTS;

export default function LiveGridPage() {
  const { data: cameras, isLoading } = useCameras();
  const [layout, setLayout] = useState<Layout>('4');

  return (
    <div className="mx-auto max-w-6xl px-8 py-10">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Live view</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Low-latency WebRTC streams from your cameras.
          </p>
        </div>
        <div className="flex gap-1 rounded-md border p-1">
          {(Object.keys(LAYOUTS) as Layout[]).map((key) => (
            <Button
              key={key}
              size="sm"
              variant={layout === key ? 'default' : 'ghost'}
              onClick={() => setLayout(key)}
            >
              {key === '1' ? '1×1' : key === '4' ? '2×2' : '3×3'}
            </Button>
          ))}
        </div>
      </div>

      {isLoading && <Skeleton className="h-64" />}

      {!isLoading && (cameras?.length ?? 0) === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <p className="text-sm text-muted-foreground">No cameras to stream yet.</p>
            <Link href="/cameras/new">
              <Button>Add a camera</Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {!isLoading && cameras && cameras.length > 0 && (
        <div className={cn('grid gap-4', LAYOUTS[layout])}>
          {cameras.map((camera) => (
            <div key={camera.id} className="space-y-2">
              <LivePlayer cameraId={camera.id} autoStart />
              <div className="flex items-center justify-between px-1">
                <Link href={`/cameras/${camera.id}`} className="truncate text-sm font-medium hover:underline">
                  {camera.name}
                </Link>
                <CameraStatusBadge status={camera.status} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
