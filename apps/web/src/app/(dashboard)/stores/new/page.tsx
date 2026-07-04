'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@visionops/ui';
import { StoreForm } from '@/features/stores/store-form';
import { useCreateStore } from '@/features/stores/hooks';
import { ApiError } from '@/lib/api-client';
import type { CreateStoreInput } from '@/features/stores/types';

export default function NewStorePage() {
  const router = useRouter();
  const createStore = useCreateStore();
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (values: CreateStoreInput) => {
    setError(null);
    try {
      const store = await createStore.mutateAsync(values);
      router.replace(`/stores/${store.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create the store.');
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-8 py-10">
      <Link href="/stores" className="text-sm text-muted-foreground hover:underline">
        ← Back to stores
      </Link>
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Add a store</CardTitle>
          <CardDescription>Create a physical location for your organization.</CardDescription>
        </CardHeader>
        <CardContent>
          <StoreForm
            onSubmit={onSubmit}
            submitting={createStore.isPending}
            error={error}
            submitLabel="Create store"
          />
        </CardContent>
      </Card>
    </div>
  );
}
