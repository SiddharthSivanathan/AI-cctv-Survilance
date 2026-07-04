'use client';

import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@visionops/ui';
import { useAuth } from '@/features/auth/use-auth';
import { useStores } from '@/features/stores/hooks';
import { useCameras } from '@/features/cameras/hooks';

export default function DashboardOverviewPage() {
  const { user } = useAuth();
  const stores = useStores();
  const cameras = useCameras();

  return (
    <div className="mx-auto max-w-5xl px-8 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">
        Welcome back, {user?.user.full_name?.split(' ')[0]}.
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Here’s an overview of your workspace.
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Stores</CardDescription>
            <CardTitle className="text-3xl">
              {stores.isLoading ? '—' : (stores.data?.length ?? 0)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Link href="/stores" className="text-sm text-muted-foreground hover:underline">
              Manage stores →
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Cameras</CardDescription>
            <CardTitle className="text-3xl">
              {cameras.isLoading ? '—' : (cameras.data?.length ?? 0)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Link href="/cameras" className="text-sm text-muted-foreground hover:underline">
              Manage cameras →
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Open alerts</CardDescription>
            <CardTitle className="text-3xl">0</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-muted-foreground">Coming soon</span>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Get started</CardTitle>
          <CardDescription>
            Add your stores, then connect cameras as camera support ships.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/stores" className="text-sm font-medium hover:underline">
            Go to stores →
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
