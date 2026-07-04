'use client';

import { useRef, useState } from 'react';
import { Button, Input, Label, Select } from '@visionops/ui';
import { useCreateZone } from '@/features/zones/hooks';
import { ZONE_TYPES, type Point } from '@/features/zones/types';

const SIZE = 640;

/** Draw a polygon zone on the camera's 640x640 sampled frame. */
export function ZoneEditor({
  cameraId,
  thumbnailUrl,
  onSaved,
}: {
  cameraId: string;
  thumbnailUrl?: string | null;
  onSaved?: () => void;
}) {
  const svgRef = useRef<SVGSVGElement>(null);
  const createZone = useCreateZone();
  const [points, setPoints] = useState<Point[]>([]);
  const [name, setName] = useState('');
  const [zoneType, setZoneType] = useState<string>('queue');

  const addPoint = (e: React.MouseEvent<SVGSVGElement>) => {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * SIZE;
    const y = ((e.clientY - rect.top) / rect.height) * SIZE;
    setPoints((prev) => [...prev, [Math.round(x), Math.round(y)]]);
  };

  const save = async () => {
    if (points.length < 3 || !name) return;
    await createZone.mutateAsync({ camera_id: cameraId, name, zone_type: zoneType, polygon: points });
    setPoints([]);
    setName('');
    onSaved?.();
  };

  const polyString = points.map((p) => p.join(',')).join(' ');

  return (
    <div className="space-y-3">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="aspect-square w-full cursor-crosshair rounded-lg border bg-muted"
        onClick={addPoint}
      >
        {thumbnailUrl && <image href={thumbnailUrl} width={SIZE} height={SIZE} preserveAspectRatio="xMidYMid slice" />}
        {points.length > 0 && (
          <polygon points={polyString} fill="rgba(34,197,94,0.25)" stroke="#22c55e" strokeWidth={3} />
        )}
        {points.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={5} fill="#22c55e" />
        ))}
      </svg>

      <p className="text-xs text-muted-foreground">
        Click to add points ({points.length}). Minimum 3 to form a zone.
      </p>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="zone-name">Zone name</Label>
          <Input id="zone-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Checkout area" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="zone-type">Type</Label>
          <Select id="zone-type" value={zoneType} onChange={(e) => setZoneType(e.target.value)}>
            {ZONE_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div className="flex gap-2">
        <Button type="button" size="sm" onClick={save} disabled={points.length < 3 || !name || createZone.isPending}>
          {createZone.isPending ? 'Saving…' : 'Save zone'}
        </Button>
        <Button type="button" size="sm" variant="ghost" onClick={() => setPoints((p) => p.slice(0, -1))}>
          Undo point
        </Button>
        <Button type="button" size="sm" variant="ghost" onClick={() => setPoints([])}>
          Clear
        </Button>
      </div>
    </div>
  );
}
