'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@visionops/ui';
import { CameraForm } from '@/features/cameras/camera-form';
import { useCreateCamera } from '@/features/cameras/hooks';
import { ApiError } from '@/lib/api-client';
import type { CreateCameraInput } from '@/features/cameras/types';

function NewCameraInner() {
  const router = useRouter();
  const params = useSearchParams();
  const createCamera = useCreateCamera();
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (values: CreateCameraInput) => {
    setError(null);
    try {
      const camera = await createCamera.mutateAsync(values);
      router.replace(`/cameras/${camera.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not add the camera.');
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-8 py-10">
      <Link href="/cameras" className="text-sm text-muted-foreground hover:underline">
        ← Back to cameras
      </Link>
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Add a camera</CardTitle>
          <CardDescription>
            Enter the RTSP details, test the connection, then save.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CameraForm
            defaultStoreId={params.get('store_id') ?? undefined}
            onSubmit={onSubmit}
            submitting={createCamera.isPending}
            error={error}
            submitLabel="Add camera"
          />
        </CardContent>
      </Card>
    </div>
  );
}

export default function NewCameraPage() {
  return (
    <Suspense>
      <NewCameraInner />
    </Suspense>
  );
}
