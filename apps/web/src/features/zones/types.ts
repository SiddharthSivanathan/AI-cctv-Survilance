export type Point = [number, number];

export interface Zone {
  id: string;
  camera_id: string;
  name: string;
  zone_type: string;
  polygon: Point[];
  config: Record<string, unknown> | null;
}

export interface CreateZoneInput {
  camera_id: string;
  name: string;
  zone_type: string;
  polygon: Point[];
}

export const ZONE_TYPES = [
  { value: 'queue', label: 'Queue' },
  { value: 'occupancy', label: 'Occupancy' },
  { value: 'billing_counter', label: 'Billing counter' },
  { value: 'restricted', label: 'Restricted' },
] as const;
