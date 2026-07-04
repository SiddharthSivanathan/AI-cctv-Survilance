'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';
import { Camera as CameraIcon } from 'lucide-react';
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
import { CameraStatusBadge } from '@/features/cameras/status';
import { useCamera, useDeleteCamera, useTestCamera } from '@/features/cameras/hooks';

export default function CameraDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;
  const { data: camera, isLoading, isError } = useCamera(id);
  const testCamera = useTestCamera(id);
  const deleteCamera = useDeleteCamera();
  const [confirming, setConfirming] = useState(false);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl px-8 py-10">
        <Skeleton className="h-64" />
      </div>
    );
  }
  if (isError || !camera) {
    return (
      <div className="mx-auto max-w-3xl px-8 py-10">
        <p className="text-sm text-destructive">Camera not found.</p>
        <Link href="/cameras" className="text-sm hover:underline">
          ← Back to cameras
        </Link>
      </div>
    );
  }

  const onDelete = async () => {
    await deleteCamera.mutateAsync(id);
    router.replace('/cameras');
  };

  return (
    <div className="mx-auto max-w-3xl px-8 py-10">
      <Link href="/cameras" className="text-sm text-muted-foreground hover:underline">
        ← Back to cameras
      </Link>

      <div className="mt-4 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">{camera.name}</h1>
          <CameraStatusBadge status={camera.status} />
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={testCamera.isPending}
            onClick={() => testCamera.mutate()}
          >
            {testCamera.isPending ? 'Testing…' : 'Test connection'}
          </Button>
          <Link href={`/cameras/${id}/edit`}>
            <Button variant="outline" size="sm">
              Edit
            </Button>
          </Link>
          {confirming ? (
            <Button variant="destructive" size="sm" onClick={onDelete} disabled={deleteCamera.isPending}>
              {deleteCamera.isPending ? 'Deleting…' : 'Confirm'}
            </Button>
          ) : (
            <Button variant="outline" size="sm" onClick={() => setConfirming(true)}>
              Delete
            </Button>
          )}
        </div>
      </div>

      <Card className="mt-6 overflow-hidden">
        <div className="flex aspect-video items-center justify-center bg-muted">
          {camera.thumbnail_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={camera.thumbnail_url} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="flex flex-col items-center gap-2 text-muted-foreground/50">
              <CameraIcon className="h-10 w-10" />
              <span className="text-xs">No preview yet</span>
            </div>
          )}
        </div>
      </Card>

      {camera.last_error && camera.status !== 'online' && (
        <p className="mt-3 text-sm text-destructive">{camera.last_error}</p>
      )}

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <Detail label="Resolution" value={camera.resolution} />
        <Detail label="FPS" value={camera.fps ? String(camera.fps) : null} />
        <Detail label="Codec" value={camera.codec} />
        <Detail
          label="Last seen"
          value={camera.last_seen_at ? formatDateTime(camera.last_seen_at) : null}
        />
        <Detail label="Credentials" value={camera.has_credentials ? 'Stored' : 'None'} />
        <Detail label="Sampling FPS" value={String(camera.sample_fps)} />
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Live stream</CardTitle>
          <CardDescription>
            Low-latency live view arrives with the streaming gateway in the next module.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <span className="text-xs text-muted-foreground">Coming soon</span>
        </CardContent>
      </Card>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string | null }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-base">{value ?? '—'}</CardTitle>
      </CardHeader>
    </Card>
  );
}
