'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Alert, Button, Input, Label, Select } from '@visionops/ui';
import { useStores } from '@/features/stores/hooks';
import { useTestConnection } from './hooks';
import { connectionLabel } from './status';
import type { Camera, CreateCameraInput } from './types';

const schema = z.object({
  store_id: z.string().min(1, 'Select a store'),
  name: z.string().min(1, 'Camera name is required'),
  rtsp_url: z.string().min(1, 'RTSP URL is required'),
  username: z.string().optional(),
  password: z.string().optional(),
  sample_fps: z.coerce.number().int().min(1).max(30).optional(),
});
type FormValues = z.infer<typeof schema>;

export function CameraForm({
  initial,
  defaultStoreId,
  onSubmit,
  submitting,
  error,
  submitLabel = 'Save camera',
}: {
  initial?: Camera;
  defaultStoreId?: string;
  onSubmit: (values: CreateCameraInput) => void | Promise<void>;
  submitting?: boolean;
  error?: string | null;
  submitLabel?: string;
}) {
  const stores = useStores();
  const testConnection = useTestConnection();
  const [testResult, setTestResult] = useState<string | null>(null);

  const { register, handleSubmit, getValues, formState } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      store_id: initial?.store_id ?? defaultStoreId ?? '',
      name: initial?.name ?? '',
      rtsp_url: initial?.rtsp_url ?? '',
      username: initial?.username ?? '',
      password: '',
      sample_fps: initial?.sample_fps ?? 2,
    },
  });

  const runTest = async () => {
    setTestResult(null);
    const { rtsp_url, username, password } = getValues();
    if (!rtsp_url) {
      setTestResult('Enter an RTSP URL first.');
      return;
    }
    const result = await testConnection.mutateAsync({
      rtsp_url,
      username: username || undefined,
      password: password || undefined,
    });
    const meta = result.resolution ? ` · ${result.resolution}` : '';
    setTestResult(`${connectionLabel(result.status)}${meta}`);
  };

  const submit = (v: FormValues) =>
    onSubmit({
      store_id: v.store_id,
      name: v.name,
      rtsp_url: v.rtsp_url,
      username: v.username || undefined,
      // Blank password on edit keeps the stored one.
      password: v.password || undefined,
      sample_fps: v.sample_fps,
    });

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-4">
      {error && <Alert variant="destructive">{error}</Alert>}

      <div className="space-y-2">
        <Label htmlFor="store_id">Store</Label>
        <Select id="store_id" {...register('store_id')} defaultValue={initial?.store_id ?? defaultStoreId}>
          <option value="">Select a store…</option>
          {stores.data?.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </Select>
        {formState.errors.store_id && (
          <p className="text-xs text-destructive">{formState.errors.store_id.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="name">Camera name</Label>
        <Input id="name" placeholder="Billing Counter Camera" {...register('name')} />
        {formState.errors.name && (
          <p className="text-xs text-destructive">{formState.errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="rtsp_url">RTSP URL</Label>
        <Input id="rtsp_url" placeholder="rtsp://192.168.1.10:554/stream1" {...register('rtsp_url')} />
        {formState.errors.rtsp_url && (
          <p className="text-xs text-destructive">{formState.errors.rtsp_url.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="username">Username (optional)</Label>
          <Input id="username" autoComplete="off" {...register('username')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password (optional)</Label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            placeholder={initial?.has_credentials ? 'Password is securely stored' : ''}
            {...register('password')}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="sample_fps">AI sampling FPS</Label>
        <Input id="sample_fps" type="number" min={1} max={30} {...register('sample_fps')} />
      </div>

      <div className="flex items-center gap-3 border-t pt-4">
        <Button type="button" variant="outline" onClick={runTest} disabled={testConnection.isPending}>
          {testConnection.isPending ? 'Testing…' : 'Test connection'}
        </Button>
        {testResult && <span className="text-sm text-muted-foreground">{testResult}</span>}
      </div>

      <Button type="submit" disabled={submitting}>
        {submitting ? 'Saving…' : submitLabel}
      </Button>
    </form>
  );
}
