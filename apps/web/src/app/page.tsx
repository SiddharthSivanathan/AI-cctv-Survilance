import Link from 'next/link';
import { Button } from '@visionops/ui';
import { env } from '@/lib/env';

/** Public landing page. */
export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between px-6 py-5">
        <span className="text-lg font-bold tracking-tight">
          VisionOps<span className="text-muted-foreground"> AI</span>
        </span>
        <div className="flex items-center gap-2">
          <Link href="/login">
            <Button variant="ghost" size="sm">
              Log in
            </Button>
          </Link>
          <Link href="/signup">
            <Button size="sm">Get started</Button>
          </Link>
        </div>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center gap-8 px-6 text-center">
        <div className="flex flex-col items-center gap-4">
          <span className="rounded-full border border-border px-3 py-1 text-xs font-medium text-muted-foreground">
            AI Video Intelligence
          </span>
          <h1 className="max-w-3xl text-balance text-5xl font-bold tracking-tight sm:text-6xl">
            Turn your CCTV into an always-on AI operations analyst
          </h1>
          <p className="max-w-xl text-balance text-lg text-muted-foreground">
            {env.appName} connects to your existing cameras to detect, understand, and act on what
            happens across your business — in real time.
          </p>
        </div>
        <div className="flex gap-3">
          <Link href="/signup">
            <Button size="lg">Get started free</Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="outline">
              Log in
            </Button>
          </Link>
        </div>
      </main>

      <footer className="px-6 py-6 text-center text-xs text-muted-foreground">
        © 2026 {env.appName}. All rights reserved.
      </footer>
    </div>
  );
}
