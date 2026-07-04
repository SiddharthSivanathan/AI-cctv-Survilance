'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';
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
import { useResetPassword } from '@/features/auth/hooks';
import { ApiError } from '@/lib/api-client';

const schema = z.object({ password: z.string().min(8, 'Use at least 8 characters') });
type FormValues = z.infer<typeof schema>;

function ResetPasswordInner() {
  const params = useSearchParams();
  const token = params.get('token') ?? '';
  const reset = useResetPassword();
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const { register, handleSubmit, formState } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  if (!token) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Invalid reset link</CardTitle>
          <CardDescription>This link is missing its token. Request a new one.</CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/forgot-password" className="text-sm font-medium hover:underline">
            Request a new reset link
          </Link>
        </CardContent>
      </Card>
    );
  }

  const onSubmit = async (values: FormValues) => {
    setError(null);
    try {
      await reset.mutateAsync({ token, password: values.password });
      setDone(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Set a new password</CardTitle>
        <CardDescription>
          {done ? 'Your password has been updated.' : 'Choose a strong new password.'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {done ? (
          <Link href="/login" className="text-sm font-medium hover:underline">
            Continue to login
          </Link>
        ) : (
          <>
            {error && (
              <Alert variant="destructive" className="mb-4">
                {error}
              </Alert>
            )}
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="password">New password</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  {...register('password')}
                />
                {formState.errors.password && (
                  <p className="text-xs text-destructive">{formState.errors.password.message}</p>
                )}
              </div>
              <Button type="submit" className="w-full" disabled={reset.isPending}>
                {reset.isPending ? 'Updating…' : 'Update password'}
              </Button>
            </form>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordInner />
    </Suspense>
  );
}
