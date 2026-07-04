'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useRef, useState } from 'react';
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@visionops/ui';
import { useVerifyEmail } from '@/features/auth/hooks';
import { ApiError } from '@/lib/api-client';

type Status = 'verifying' | 'success' | 'error';

function VerifyEmailInner() {
  const params = useSearchParams();
  const router = useRouter();
  const verify = useVerifyEmail();
  const token = params.get('token') ?? '';
  const [status, setStatus] = useState<Status>('verifying');
  const [message, setMessage] = useState('');
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    if (!token) {
      setStatus('error');
      setMessage('This verification link is missing its token.');
      return;
    }

    verify
      .mutateAsync(token)
      .then((result) => {
        setStatus('success');
        setTimeout(
          () => router.replace(result.user.needs_onboarding ? '/onboarding' : '/dashboard'),
          800,
        );
      })
      .catch((err) => {
        setStatus('error');
        setMessage(
          err instanceof ApiError
            ? err.message
            : 'Verification failed. The link may have expired.',
        );
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {status === 'verifying' && 'Verifying your email…'}
          {status === 'success' && 'Email verified'}
          {status === 'error' && 'Verification failed'}
        </CardTitle>
        <CardDescription>
          {status === 'verifying' && 'Hang tight while we confirm your account.'}
          {status === 'success' && 'Signing you in and taking you to setup…'}
          {status === 'error' && message}
        </CardDescription>
      </CardHeader>
      {status === 'error' && (
        <CardContent className="space-y-3">
          <Button onClick={() => router.replace('/login')} className="w-full">
            Back to login
          </Button>
          <p className="text-center text-sm text-muted-foreground">
            Need a new link?{' '}
            <Link href="/login" className="font-medium text-foreground hover:underline">
              Log in to resend
            </Link>
          </p>
        </CardContent>
      )}
    </Card>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyEmailInner />
    </Suspense>
  );
}
