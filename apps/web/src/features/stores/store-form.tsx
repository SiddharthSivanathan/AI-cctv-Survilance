'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Alert, Button, Input, Label } from '@visionops/ui';
import type { CreateStoreInput, Store } from './types';

const schema = z.object({
  name: z.string().min(1, 'Store name is required'),
  code: z.string().optional(),
  address: z.string().optional(),
  city: z.string().optional(),
  country: z.string().optional(),
  timezone: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

export function StoreForm({
  initial,
  onSubmit,
  submitting,
  error,
  submitLabel = 'Save store',
}: {
  initial?: Store;
  onSubmit: (values: CreateStoreInput) => void | Promise<void>;
  submitting?: boolean;
  error?: string | null;
  submitLabel?: string;
}) {
  const { register, handleSubmit, formState } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initial?.name ?? '',
      code: initial?.code ?? '',
      address: initial?.address ?? '',
      city: initial?.city ?? '',
      country: initial?.country ?? '',
      timezone: initial?.timezone ?? 'UTC',
    },
  });

  return (
    <form
      onSubmit={handleSubmit((v) =>
        onSubmit({
          name: v.name,
          code: v.code || undefined,
          address: v.address || undefined,
          city: v.city || undefined,
          country: v.country || undefined,
          timezone: v.timezone || undefined,
        }),
      )}
      className="space-y-4"
    >
      {error && <Alert variant="destructive">{error}</Alert>}
      <div className="space-y-2">
        <Label htmlFor="name">Store name</Label>
        <Input id="name" placeholder="ABC Supermarket — Madurai" {...register('name')} />
        {formState.errors.name && (
          <p className="text-xs text-destructive">{formState.errors.name.message}</p>
        )}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="code">Store code</Label>
          <Input id="code" placeholder="MDU-01" {...register('code')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="timezone">Timezone</Label>
          <Input id="timezone" placeholder="Asia/Kolkata" {...register('timezone')} />
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="address">Address</Label>
        <Input id="address" {...register('address')} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="city">City</Label>
          <Input id="city" {...register('city')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="country">Country</Label>
          <Input id="country" {...register('country')} />
        </div>
      </div>
      <Button type="submit" disabled={submitting}>
        {submitting ? 'Saving…' : submitLabel}
      </Button>
    </form>
  );
}
