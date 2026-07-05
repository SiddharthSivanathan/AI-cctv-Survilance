export type ConnectionStatus = 'connecting' | 'connected' | 'reconnecting' | 'disconnected';

export interface RealtimeEvent {
  type: string; // alert.created | alert.resolved | camera.offline | camera.online | camera.reconnected | ping
  organizationId: string;
  cameraId: string | null;
  storeId: string | null;
  severity: string | null;
  title: string | null;
  message: string | null;
  timestamp: string;
  metadata: Record<string, unknown>;
}
