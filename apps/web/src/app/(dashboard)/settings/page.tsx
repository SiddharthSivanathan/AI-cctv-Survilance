'use client';

import { useEffect, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import {
  Alert,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Select,
  Skeleton,
  Switch,
} from '@visionops/ui';
import { formatDateTime } from '@visionops/utils';
import { useOrganization, useUpdateOrganization, useUploadLogo } from '@/features/organizations/hooks';

const CURRENCIES = ['USD', 'EUR', 'GBP', 'INR', 'AED', 'SGD', 'AUD', 'CAD'];

interface FormValues {
  name: string;
  industry: string;
  contact_email: string;
  contact_phone: string;
  address: string;
  timezone: string;
  currency: string;
}

export default function SettingsPage() {
  const { data: org, isLoading } = useOrganization();
  const update = useUpdateOrganization();
  const uploadLogo = useUploadLogo();
  const fileRef = useRef<HTMLInputElement>(null);

  const [alertsOn, setAlertsOn] = useState(true);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, reset } = useForm<FormValues>();

  useEffect(() => {
    if (org) {
      reset({
        name: org.name,
        industry: org.industry ?? '',
        contact_email: org.contact_email ?? '',
        contact_phone: org.contact_phone ?? '',
        address: org.address ?? '',
        timezone: org.timezone,
        currency: org.currency,
      });
      setAlertsOn(org.alert_email_enabled);
    }
  }, [org, reset]);

  const onSubmit = async (values: FormValues) => {
    setError(null);
    setSaved(false);
    try {
      await update.mutateAsync({
        name: values.name,
        industry: values.industry || null,
        contact_email: values.contact_email || null,
        contact_phone: values.contact_phone || null,
        address: values.address || null,
        timezone: values.timezone,
        currency: values.currency,
        alert_email_enabled: alertsOn,
      });
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save settings.');
    }
  };

  const onLogo = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    try {
      await uploadLogo.mutateAsync(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Logo upload failed.');
    }
  };

  if (isLoading || !org) {
    return (
      <div className="mx-auto max-w-2xl px-8 py-10">
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-8 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">Organization settings</h1>
      <p className="mt-1 text-sm text-muted-foreground">Manage your company profile.</p>

      {error && (
        <Alert variant="destructive" className="mt-4">
          {error}
        </Alert>
      )}
      {saved && (
        <Alert variant="success" className="mt-4">
          Settings saved.
        </Alert>
      )}

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Logo</CardTitle>
          <CardDescription>PNG, JPEG, WEBP or SVG, up to 2 MB.</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-4">
          {org.logo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={org.logo_url} alt="Logo" className="h-16 w-16 rounded-lg object-cover" />
          ) : (
            <span className="flex h-16 w-16 items-center justify-center rounded-lg bg-primary text-xl font-semibold text-primary-foreground">
              {org.name.charAt(0).toUpperCase()}
            </span>
          )}
          <div>
            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/svg+xml"
              className="hidden"
              onChange={onLogo}
            />
            <Button
              variant="outline"
              size="sm"
              disabled={uploadLogo.isPending}
              onClick={() => fileRef.current?.click()}
            >
              {uploadLogo.isPending ? 'Uploading…' : 'Upload logo'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit(onSubmit)}>
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base">Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Company name</Label>
              <Input id="name" {...register('name')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="industry">Industry</Label>
              <Input id="industry" placeholder="Retail, Warehouse…" {...register('industry')} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="contact_email">Contact email</Label>
                <Input id="contact_email" type="email" {...register('contact_email')} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact_phone">Contact phone</Label>
                <Input id="contact_phone" {...register('contact_phone')} />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="address">Address</Label>
              <Input id="address" {...register('address')} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="timezone">Timezone</Label>
                <Input id="timezone" placeholder="Asia/Kolkata" {...register('timezone')} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="currency">Currency</Label>
                <Select id="currency" {...register('currency')}>
                  {CURRENCIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base">Notifications</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Email alerts</p>
              <p className="text-sm text-muted-foreground">
                Receive AI alerts by email when they trigger.
              </p>
            </div>
            <Switch checked={alertsOn} onCheckedChange={setAlertsOn} aria-label="Email alerts" />
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base">Account</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Organization ID</span>
              <span className="font-mono text-xs">{org.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Created</span>
              <span>{formatDateTime(org.created_at)}</span>
            </div>
          </CardContent>
        </Card>

        <div className="mt-6">
          <Button type="submit" disabled={update.isPending}>
            {update.isPending ? 'Saving…' : 'Save changes'}
          </Button>
        </div>
      </form>
    </div>
  );
}
