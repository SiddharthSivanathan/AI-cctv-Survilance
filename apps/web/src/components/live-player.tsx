'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Camera as CameraIcon, Loader2 } from 'lucide-react';
import { Button } from '@visionops/ui';
import { streamsApi } from '@/features/streams/api';
import { connectWhep, type WhepSession } from '@/features/streams/whep';

type PlayerState = 'idle' | 'connecting' | 'live' | 'reconnecting' | 'error';

const MAX_RETRIES = 5;

export function LivePlayer({ cameraId, autoStart = false }: { cameraId: string; autoStart?: boolean }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const sessionRef = useRef<WhepSession | null>(null);
  const retriesRef = useRef(0);
  const mountedRef = useRef(true);
  const [state, setState] = useState<PlayerState>('idle');

  const teardown = useCallback(async () => {
    const session = sessionRef.current;
    sessionRef.current = null;
    if (session) await session.close();
  }, []);

  const start = useCallback(async () => {
    await teardown();
    if (!mountedRef.current) return;
    setState(retriesRef.current > 0 ? 'reconnecting' : 'connecting');
    try {
      const { whep_url, token } = await streamsApi.startLive(cameraId);
      const session = await connectWhep(
        whep_url,
        token,
        (stream) => {
          if (videoRef.current) videoRef.current.srcObject = stream;
        },
        (connState) => {
          if (!mountedRef.current) return;
          if (connState === 'connected') {
            retriesRef.current = 0;
            setState('live');
          } else if (connState === 'failed' || connState === 'disconnected') {
            if (retriesRef.current < MAX_RETRIES) {
              retriesRef.current += 1;
              setTimeout(() => mountedRef.current && start(), 1500);
            } else {
              setState('error');
            }
          }
        },
      );
      sessionRef.current = session;
    } catch {
      if (!mountedRef.current) return;
      if (retriesRef.current < MAX_RETRIES) {
        retriesRef.current += 1;
        setState('reconnecting');
        setTimeout(() => mountedRef.current && start(), 1500);
      } else {
        setState('error');
      }
    }
  }, [cameraId, teardown]);

  useEffect(() => {
    mountedRef.current = true;
    if (autoStart) void start();
    return () => {
      mountedRef.current = false;
      void teardown();
    };
  }, [autoStart, start, teardown]);

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-black">
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className="h-full w-full object-contain"
      />

      {state !== 'live' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-muted text-muted-foreground">
          {state === 'idle' && (
            <>
              <CameraIcon className="h-8 w-8 opacity-40" />
              <Button size="sm" onClick={() => void start()}>
                Go live
              </Button>
            </>
          )}
          {(state === 'connecting' || state === 'reconnecting') && (
            <>
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="text-xs">
                {state === 'connecting' ? 'Connecting…' : 'Reconnecting…'}
              </span>
            </>
          )}
          {state === 'error' && (
            <>
              <span className="text-xs text-destructive">Stream unavailable</span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  retriesRef.current = 0;
                  void start();
                }}
              >
                Retry
              </Button>
            </>
          )}
        </div>
      )}

      {state === 'live' && (
        <span className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full bg-black/60 px-2 py-0.5 text-xs font-medium text-white">
          <span className="h-2 w-2 animate-pulse rounded-full bg-red-500" />
          LIVE
        </span>
      )}
    </div>
  );
}
