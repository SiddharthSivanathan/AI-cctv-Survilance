'use client';

export interface LinePoint {
  label: string;
  value: number;
}

/** Dependency-free responsive line chart with area fill. */
export function LineChart({
  data,
  height = 160,
  color = 'hsl(var(--primary))',
}: {
  data: LinePoint[];
  height?: number;
  color?: string;
}) {
  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-sm text-muted-foreground"
        style={{ height }}
      >
        No data yet
      </div>
    );
  }

  const w = 600;
  const h = height;
  const pad = 8;
  const max = Math.max(1, ...data.map((d) => d.value));
  const stepX = data.length > 1 ? (w - 2 * pad) / (data.length - 1) : 0;
  const pts = data.map((d, i) => {
    const x = pad + i * stepX;
    const y = h - pad - (d.value / max) * (h - 2 * pad);
    return [x, y] as const;
  });
  const line = pts.map((p) => p.join(',')).join(' ');
  const lastX = pad + (data.length - 1) * stepX;
  const area = `${pad},${h - pad} ${line} ${lastX},${h - pad}`;

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
      style={{ width: '100%', height }}
      role="img"
    >
      <polygon points={area} fill={color} fillOpacity={0.12} />
      <polyline
        points={line}
        fill="none"
        stroke={color}
        strokeWidth={2}
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
