'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
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
import { useDeleteStore, useStore } from '@/features/stores/hooks';
import { useCameras } from '@/features/cameras/hooks';
import { CameraCard } from '@/components/camera-card';

export default function StoreDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;
  const { data: store, isLoading, isError } = useStore(id);
  const cameras = useCameras(id);
  const deleteStore = useDeleteStore();
  const [confirming, setConfirming] = useState(false);

  const onDelete = async () => {
    await deleteStore.mutateAsync(id);
    router.replace('/stores');
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl px-8 py-10">
        <Skeleton className="h-40" />
      </div>
    );
  }
  if (isError || !store) {
    return (
      <div className="mx-auto max-w-3xl px-8 py-10">
        <p className="text-sm text-destructive">Store not found.</p>
        <Link href="/stores" className="text-sm hover:underline">
          ← Back to stores
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-8 py-10">
      <Link href="/stores" className="text-sm text-muted-foreground hover:underline">
        ← Back to stores
      </Link>

      <div className="mt-4 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{store.name}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {[store.address, store.city, store.country].filter(Boolean).join(', ') ||
              'No location set'}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href={`/stores/${id}/edit`}>
            <Button variant="outline" size="sm">
              Edit
            </Button>
          </Link>
          {confirming ? (
            <Button
              variant="destructive"
              size="sm"
              disabled={deleteStore.isPending}
              onClick={onDelete}
            >
              {deleteStore.isPending ? 'Deleting…' : 'Confirm delete'}
            </Button>
          ) : (
            <Button variant="outline" size="sm" onClick={() => setConfirming(true)}>
              Delete
            </Button>
          )}
        </div>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Store code</CardDescription>
            <CardTitle className="text-base">{store.code || '—'}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Timezone</CardDescription>
            <CardTitle className="text-base">{store.timezone}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="mt-8 flex items-center justify-between">
        <h2 className="text-lg font-semibold tracking-tight">Cameras</h2>
        <Link href={`/cameras/new?store_id=${id}`}>
          <Button size="sm">Add camera</Button>
        </Link>
      </div>

      {cameras.data && cameras.data.length > 0 ? (
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          {cameras.data.map((camera) => (
            <CameraCard key={camera.id} camera={camera} />
          ))}
        </div>
      ) : (
        <Card className="mt-4">
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            No cameras connected to this store yet.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
