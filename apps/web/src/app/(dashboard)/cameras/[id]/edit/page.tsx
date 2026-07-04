'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Skeleton,
} from '@visionops/ui';
import { CameraForm } from '@/features/cameras/camera-form';
import { useCamera, useUpdateCamera } from '@/features/cameras/hooks';
import { ApiError } from '@/lib/api-client';
import type { CreateCameraInput } from '@/features/cameras/types';

export default function EditCameraPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;
  const { data: camera, isLoading } = useCamera(id);
  const updateCamera = useUpdateCamera(id);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (values: CreateCameraInput) => {
    setError(null);
    try {
      await updateCamera.mutateAsync(values);
      router.replace(`/cameras/${id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update the camera.');
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-8 py-10">
      <Link href={`/cameras/${id}`} className="text-sm text-muted-foreground hover:underline">
        ← Back to camera
      </Link>
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Edit camera</CardTitle>
          <CardDescription>
            Leave the password blank to keep the stored credentials.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading || !camera ? (
            <Skeleton className="h-96" />
          ) : (
            <CameraForm
              initial={camera}
              onSubmit={onSubmit}
              submitting={updateCamera.isPending}
              error={error}
              submitLabel="Save changes"
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
