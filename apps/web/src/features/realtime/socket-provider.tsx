'use client';

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { env } from '@/lib/env';
import { useAuthStore } from '@/stores/auth-store';
import { useUiStore } from '@/stores/ui-store';
import type { ConnectionStatus, RealtimeEvent } from './types';

const StatusContext = createContext<ConnectionStatus>('disconnected');
export const useRealtimeStatus = () => useContext(StatusContext);

const PING_INTERVAL = 30_000;
const MAX_BACKOFF = 8_000;

function socketUrl(token: string): string {
  const base = env.apiUrl.replace(/^http/, 'ws').replace(/\/$/, '');
  return `${base}/ws/events?token=${encodeURIComponent(token)}`;
}

function playBeep(): void {
  try {
    const AudioCtor = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ctx = new AudioCtor();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 880;
    gain.gain.value = 0.05;
    osc.start();
    setTimeout(() => {
      osc.stop();
      void ctx.close();
    }, 150);
  } catch {
    /* audio unavailable */
  }
}

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const socketRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const pingRef = useRef<number | undefined>(undefined);
  const closedRef = useRef(false);

  useEffect(() => {
    closedRef.current = false;

    const handle = (event: RealtimeEvent) => {
      const description = event.message ?? undefined;
      const critical = event.severity === 'high' || event.severity === 'critical';
      if (critical) toast.error(event.title ?? 'Alert', { description });
      else if (event.type.startsWith('camera.')) toast(event.title ?? 'Camera update', { description });
      else toast.info(event.title ?? 'Update', { description });

      if (critical && useUiStore.getState().soundEnabled) playBeep();

      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['events'] });
      if (event.type.startsWith('camera.')) {
        queryClient.invalidateQueries({ queryKey: ['cameras'] });
      }
    };

    const connect = () => {
      const token = useAuthStore.getState().accessToken;
      if (!token) {
        setStatus('disconnected');
        return;
      }
      setStatus(retriesRef.current > 0 ? 'reconnecting' : 'connecting');
      const ws = new WebSocket(socketUrl(token));
      socketRef.current = ws;

      ws.onopen = () => {
        retriesRef.current = 0;
        setStatus('connected');
        pingRef.current = window.setInterval(() => {
          try {
            ws.send('ping');
          } catch {
            /* noop */
          }
        }, PING_INTERVAL);
      };

      ws.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data) as RealtimeEvent;
          if (event.type !== 'ping') handle(event);
        } catch {
          /* ignore malformed */
        }
      };

      ws.onclose = () => {
        window.clearInterval(pingRef.current);
        if (closedRef.current) return;
        retriesRef.current += 1;
        setStatus('reconnecting');
        window.setTimeout(connect, Math.min(1000 * retriesRef.current, MAX_BACKOFF));
      };

      ws.onerror = () => ws.close();
    };

    connect();

    return () => {
      closedRef.current = true;
      window.clearInterval(pingRef.current);
      socketRef.current?.close();
    };
  }, [queryClient]);

  return <StatusContext.Provider value={status}>{children}</StatusContext.Provider>;
}
