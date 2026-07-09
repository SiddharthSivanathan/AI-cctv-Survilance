'use client';

import { useRef, useState } from 'react';
import { Button, Label, Select } from '@visionops/ui';

const SIZE = 640;
type Point = [number, number];

export interface LineValue {
  line: Point[]; // [] until two points are placed, else [[x1,y1],[x2,y2]]
  direction: string; // 'both' | 'in' | 'out'
}

/**
 * Draw a two-point crossing line ("tripwire") on the camera's 640x640 frame.
 * Unlike ZoneEditor (which persists a polygon zone), this reports the line to
 * the parent so it can be stored in the rule's config.
 */
export function LineEditor({
  thumbnailUrl,
  onChange,
}: {
  thumbnailUrl?: string | null;
  onChange: (value: LineValue) => void;
}) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [points, setPoints] = useState<Point[]>([]);
  const [direction, setDirection] = useState('both');

  const emit = (pts: Point[], dir: string) =>
    onChange({ line: pts.length === 2 ? pts : [], direction: dir });

  const addPoint = (e: React.MouseEvent<SVGSVGElement>) => {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const x = Math.round(((e.clientX - rect.left) / rect.width) * SIZE);
    const y = Math.round(((e.clientY - rect.top) / rect.height) * SIZE);
    setPoints((prev) => {
      const next: Point[] = prev.length >= 2 ? [[x, y]] : [...prev, [x, y]];
      emit(next, direction);
      return next;
    });
  };

  return (
    <div className="space-y-3">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="aspect-square w-full cursor-crosshair rounded-lg border bg-muted"
        onClick={addPoint}
      >
        {thumbnailUrl && (
          <image href={thumbnailUrl} width={SIZE} height={SIZE} preserveAspectRatio="xMidYMid slice" />
        )}
        {points.length === 2 && (
          <line
            x1={points[0][0]}
            y1={points[0][1]}
            x2={points[1][0]}
            y2={points[1][1]}
            stroke="#f59e0b"
            strokeWidth={4}
          />
        )}
        {points.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={6} fill="#f59e0b" />
        ))}
      </svg>

      <p className="text-xs text-muted-foreground">
        Click two points to draw the tripwire ({points.length}/2).
      </p>

      <div className="grid grid-cols-2 items-end gap-3">
        <div className="space-y-1.5">
          <Label>Alert on</Label>
          <Select
            value={direction}
            onChange={(e) => {
              setDirection(e.target.value);
              emit(points, e.target.value);
            }}
          >
            <option value="both">Both directions</option>
            <option value="in">Crossing in</option>
            <option value="out">Crossing out</option>
          </Select>
        </div>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          onClick={() => {
            setPoints([]);
            emit([], direction);
          }}
        >
          Clear line
        </Button>
      </div>
    </div>
  );
}
