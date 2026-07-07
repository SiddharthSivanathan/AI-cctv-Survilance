'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
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
} from '@visionops/ui';
import { AuthGuard } from '@/components/auth-guard';
import { useCreateOrganization } from '@/features/auth/hooks';
import { useAuth } from '@/features/auth/use-auth';
import { useCreateStore } from '@/features/stores/hooks';
import { StoreForm } from '@/features/stores/store-form';
import { useCreateCamera } from '@/features/cameras/hooks';
import { CameraForm } from '@/features/cameras/camera-form';
import { ApiError } from '@/lib/api-client';
import type { CreateStoreInput } from '@/features/stores/types';
import type { CreateCameraInput } from '@/features/cameras/types';

const companySchema = z.object({
  name: z.string().min(1, 'Company name is required'),
  industry: z.string().optional(),
});
type CompanyValues = z.infer<typeof companySchema>;

const STEPS = ['Company', 'First store', 'First camera', 'Finish'] as const;

function Stepper({ current }: { current: number }) {
  return (
    <ol className="mb-8 flex items-center justify-center gap-2 text-xs">
      {STEPS.map((label, i) => (
        <li key={label} className="flex items-center gap-2">
          <span
            className={`flex h-6 w-6 items-center justify-center rounded-full border ${
              i <= current
                ? 'border-primary bg-primary text-primary-foreground'
                : 'border-border text-muted-foreground'
            }`}
          >
            {i + 1}
          </span>
          <span className={i <= current ? 'font-medium' : 'text-muted-foreground'}>{label}</span>
          {i < STEPS.length - 1 && <span className="mx-1 text-muted-foreground">—</span>}
        </li>
      ))}
    </ol>
  );
}

function OnboardingFlow() {
  const router = useRouter();
  const { user } = useAuth();
  const createOrg = useCreateOrganization();
  const createStore = useCreateStore();
  const createCamera = useCreateCamera();
  const [step, setStep] = useState(user?.needs_onboarding ? 0 : 1);
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, formState } = useForm<CompanyValues>({
    resolver: zodResolver(companySchema),
  });

  const submitCompany = async (values: CompanyValues) => {
    setError(null);
    try {
      await createOrg.mutateAsync({ name: values.name, industry: values.industry || undefined });
      setStep(1);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create your company.');
    }
  };

  const submitStore = async (values: CreateStoreInput) => {
    setError(null);
    try {
      await createStore.mutateAsync(values);
      setStep(2);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create the store.');
    }
  };

  const submitCamera = async (values: CreateCameraInput) => {
    setError(null);
    try {
      await createCamera.mutateAsync(values);
      setStep(3);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not add the camera.');
    }
  };

  return (
    <div className="mx-auto w-full max-w-lg px-6 py-16">
      <Stepper current={step} />

      {step === 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Set up your company</CardTitle>
            <CardDescription>
              This becomes your VisionOps workspace. You’re the owner.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4">
                {error}
              </Alert>
            )}
            <form onSubmit={handleSubmit(submitCompany)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Company name</Label>
                <Input id="name" placeholder="Acme Retail" {...register('name')} />
                {formState.errors.name && (
                  <p className="text-xs text-destructive">{formState.errors.name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="industry">Industry (optional)</Label>
                <Input
                  id="industry"
                  placeholder="Retail, Warehouse, Hospital…"
                  {...register('industry')}
                />
              </div>
              <Button type="submit" className="w-full" disabled={createOrg.isPending}>
                {createOrg.isPending ? 'Creating…' : 'Continue'}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Add your first store</CardTitle>
            <CardDescription>
              A store is a physical location (e.g. “ABC Supermarket — Madurai”). You can add more
              later.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <StoreForm
              onSubmit={submitStore}
              submitting={createStore.isPending}
              error={error}
              submitLabel="Add store & continue"
            />
            <div className="flex justify-between border-t pt-4">
              <Button variant="ghost" onClick={() => setStep(0)}>
                Back
              </Button>
              <Button variant="outline" onClick={() => setStep(2)}>
                Skip for now
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Connect your first camera</CardTitle>
            <CardDescription>
              Enter the RTSP details and test the connection. You can add more cameras later.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <CameraForm
              onSubmit={submitCamera}
              submitting={createCamera.isPending}
              error={error}
              submitLabel="Add camera & continue"
            />
            <div className="flex justify-between border-t pt-4">
              <Button variant="ghost" onClick={() => setStep(1)}>
                Back
              </Button>
              <Button variant="outline" onClick={() => setStep(3)}>
                Skip for now
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>You’re all set 🎉</CardTitle>
            <CardDescription>
              Your workspace is ready. Head to the dashboard to manage cameras, rules, and live
              monitoring.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full" onClick={() => router.replace('/dashboard')}>
              Go to dashboard
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function OnboardingPage() {
  return (
    <AuthGuard requireOnboarded={false}>
      <OnboardingFlow />
    </AuthGuard>
  );
}
