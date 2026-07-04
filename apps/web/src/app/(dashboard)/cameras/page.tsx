'use client';

import Link from 'next/link';
import { Button, Card, CardContent, Skeleton } from '@visionops/ui';
import { CameraCard } from '@/components/camera-card';
import { useCameras } from '@/features/cameras/hooks';
import { useStores } from '@/features/stores/hooks';

export default function CamerasPage() {
  const { data: cameras, isLoading } = useCameras();
  const stores = useStores();
  const hasStores = (stores.data?.length ?? 0) > 0;

  return (
    <div className="mx-auto max-w-5xl px-8 py-10">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Cameras</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Connect and monitor your RTSP cameras.
          </p>
        </div>
        {hasStores && (
          <Link href="/cameras/new">
            <Button>Add camera</Button>
          </Link>
        )}
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-52" />
          <Skeleton className="h-52" />
          <Skeleton className="h-52" />
        </div>
      )}

      {!isLoading && !hasStores && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <p className="text-sm text-muted-foreground">
              Add a store before connecting cameras.
            </p>
            <Link href="/stores/new">
              <Button>Add a store</Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {!isLoading && hasStores && cameras?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <p className="text-sm text-muted-foreground">No cameras yet.</p>
            <Link href="/cameras/new">
              <Button>Add your first camera</Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {!isLoading && cameras && cameras.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cameras.map((camera) => (
            <CameraCard key={camera.id} camera={camera} />
          ))}
        </div>
      )}
    </div>
  );
}
