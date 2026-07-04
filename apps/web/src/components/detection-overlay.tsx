'use client';

import { useEffect, useRef } from 'react';
import { useLatestDetections } from '@/features/detections/hooks';
import { DETECTION_FRAME_SIZE } from '@/features/detections/types';

/**
 * Draws YOLO detection boxes over the live video. Boxes are in the 640x640
 * sampled-frame space and scaled to the displayed size (approximate — the
 * sampler squares the frame). Person count is shown as a badge.
 */
export function DetectionOverlay({ cameraId, enabled }: { cameraId: string; enabled: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { data } = useLatestDetections(cameraId, enabled);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const parent = canvas.parentElement;
    if (!parent) return;

    const w = parent.clientWidth;
    const h = parent.clientHeight;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, w, h);
    if (!data) return;

    const sx = w / DETECTION_FRAME_SIZE;
    const sy = h / DETECTION_FRAME_SIZE;
    ctx.lineWidth = 2;
    ctx.font = '12px sans-serif';

    for (const det of data.detections) {
      const [x1, y1, x2, y2] = det.bbox;
      const color = det.class_name === 'person' ? '#22c55e' : '#3b82f6';
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.strokeRect(x1 * sx, y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy);
      const label = det.track_id ? `${det.class_name} #${det.track_id}` : det.class_name;
      ctx.fillText(label, x1 * sx, Math.max(10, y1 * sy - 4));
    }
  }, [data]);

  if (!enabled) return null;

  return (
    <>
      <canvas ref={canvasRef} className="pointer-events-none absolute inset-0 h-full w-full" />
      {data && data.person_count > 0 && (
        <span className="absolute right-3 top-3 rounded-full bg-black/60 px-2 py-0.5 text-xs font-medium text-white">
          {data.person_count} {data.person_count === 1 ? 'person' : 'people'}
        </span>
      )}
    </>
  );
}
