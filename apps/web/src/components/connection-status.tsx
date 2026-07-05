'use client';

import { cn } from '@visionops/utils';
import { useRealtimeStatus } from '@/features/realtime/socket-provider';

const CONFIG: Record<string, { label: string; dot: string; show: boolean }> = {
  connected: { label: 'Live', dot: 'bg-green-500', show: true },
  connecting: { label: 'Connecting…', dot: 'bg-yellow-500', show: true },
  reconnecting: { label: 'Reconnecting…', dot: 'bg-yellow-500 animate-pulse', show: true },
  disconnected: { label: 'Offline', dot: 'bg-muted-foreground', show: true },
};

export function ConnectionStatus() {
  const status = useRealtimeStatus();
  const cfg = CONFIG[status] ?? CONFIG.disconnected;
  return (
    <div className="flex items-center gap-2 px-2 text-xs text-muted-foreground">
      <span className={cn('h-2 w-2 rounded-full', cfg.dot)} />
      {cfg.label}
    </div>
  );
}
