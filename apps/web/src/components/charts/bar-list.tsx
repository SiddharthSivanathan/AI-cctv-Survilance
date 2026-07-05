'use client';

export interface BarItem {
  label: string;
  value: number;
  color?: string;
}

/** Horizontal bar list for categorical breakdowns. */
export function BarList({ data }: { data: BarItem[] }) {
  if (data.length === 0) {
    return <p className="text-sm text-muted-foreground">No data yet.</p>;
  }
  const max = Math.max(1, ...data.map((d) => d.value));
  return (
    <div className="space-y-3">
      {data.map((d) => (
        <div key={d.label}>
          <div className="mb-1 flex items-center justify-between text-xs">
            <span className="capitalize text-muted-foreground">{d.label}</span>
            <span className="font-medium">{d.value}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-2 rounded-full"
              style={{ width: `${(d.value / max) * 100}%`, background: d.color ?? 'hsl(var(--primary))' }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
