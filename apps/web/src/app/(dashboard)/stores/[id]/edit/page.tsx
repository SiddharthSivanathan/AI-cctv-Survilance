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
import { StoreForm } from '@/features/stores/store-form';
import { useStore, useUpdateStore } from '@/features/stores/hooks';
import { ApiError } from '@/lib/api-client';
import type { CreateStoreInput } from '@/features/stores/types';

export default function EditStorePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;
  const { data: store, isLoading } = useStore(id);
  const updateStore = useUpdateStore(id);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (values: CreateStoreInput) => {
    setError(null);
    try {
      await updateStore.mutateAsync(values);
      router.replace(`/stores/${id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update the store.');
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-8 py-10">
      <Link href={`/stores/${id}`} className="text-sm text-muted-foreground hover:underline">
        ← Back to store
      </Link>
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Edit store</CardTitle>
          <CardDescription>Update this location’s details.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading || !store ? (
            <Skeleton className="h-64" />
          ) : (
            <StoreForm
              initial={store}
              onSubmit={onSubmit}
              submitting={updateStore.isPending}
              error={error}
              submitLabel="Save changes"
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
