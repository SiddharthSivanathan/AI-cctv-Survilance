'use client';

import Link from 'next/link';
import { Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from '@visionops/ui';
import { useStores } from '@/features/stores/hooks';

export default function StoresPage() {
  const { data: stores, isLoading, isError } = useStores();

  return (
    <div className="mx-auto max-w-5xl px-8 py-10">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Stores</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Your physical locations. Each store will own cameras, alerts, and reports.
          </p>
        </div>
        <Link href="/stores/new">
          <Button>Add store</Button>
        </Link>
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      )}

      {isError && <p className="text-sm text-destructive">Failed to load stores.</p>}

      {!isLoading && stores?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <p className="text-sm text-muted-foreground">You haven’t added any stores yet.</p>
            <Link href="/stores/new">
              <Button>Add your first store</Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {!isLoading && stores && stores.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          {stores.map((store) => (
            <Link key={store.id} href={`/stores/${store.id}`}>
              <Card className="transition-colors hover:border-foreground/20">
                <CardHeader>
                  <CardTitle className="text-base">{store.name}</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {[store.city, store.country].filter(Boolean).join(', ') || 'No location set'}
                  </p>
                </CardHeader>
                <CardContent>
                  <span className="rounded-full border px-2 py-0.5 text-xs capitalize text-muted-foreground">
                    {store.status}
                  </span>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
