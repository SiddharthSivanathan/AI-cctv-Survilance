'use client';

import { cn } from '@visionops/utils';
import { useRealtimeStatus } from '@/features/realtime/socket-provider';

type Cfg = { label: string; dot: string };

const DEFAULT_CFG: Cfg = { label: 'Offline', dot: 'bg-muted-foreground' };

const CONFIG: Record<string, Cfg> = {
  connected: { label: 'Live', dot: 'bg-green-500' },
  connecting: { label: 'Connecting…', dot: 'bg-yellow-500' },
  reconnecting: { label: 'Reconnecting…', dot: 'bg-yellow-500 animate-pulse' },
  disconnected: DEFAULT_CFG,
};

export function ConnectionStatus() {
  const status = useRealtimeStatus();
  const cfg: Cfg = CONFIG[status] ?? DEFAULT_CFG;
  return (
    <div className="flex items-center gap-2 px-2 text-xs text-muted-foreground">
      <span className={cn('h-2 w-2 rounded-full', cfg.dot)} />
      {cfg.label}
    </div>
  );
}
