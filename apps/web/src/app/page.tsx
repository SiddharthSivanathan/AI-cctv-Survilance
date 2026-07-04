import { Button } from '@visionops/ui';
import { env } from '@/lib/env';

/** Landing page. Replaced by the marketing site / auth redirect in later phases. */
export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 px-6 text-center">
      <div className="flex flex-col items-center gap-4">
        <span className="rounded-full border border-border px-3 py-1 text-xs font-medium text-muted-foreground">
          Phase 2 · Foundation
        </span>
        <h1 className="max-w-2xl text-balance text-5xl font-bold tracking-tight sm:text-6xl">
          {env.appName}
        </h1>
        <p className="max-w-xl text-balance text-lg text-muted-foreground">
          Turn existing CCTV into an always-on AI operations analyst. Detect, understand, and act —
          in real time.
        </p>
      </div>
      <div className="flex gap-3">
        <Button size="lg">Get started</Button>
        <Button size="lg" variant="outline">
          View docs
        </Button>
      </div>
    </main>
  );
}
