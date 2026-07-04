'use client';

import { useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Select,
} from '@visionops/ui';
import { ZoneEditor } from '@/components/zone-editor';
import { useCamera, useCameras } from '@/features/cameras/hooks';
import { useZones } from '@/features/zones/hooks';
import { useCreateRule } from './hooks';
import { RULE_TYPES, SEVERITIES } from './types';
import { ApiError } from '@/lib/api-client';

export function RuleBuilder({ onCreated }: { onCreated?: () => void }) {
  const cameras = useCameras();
  const createRule = useCreateRule();

  const [cameraId, setCameraId] = useState('');
  const [ruleType, setRuleType] = useState(RULE_TYPES[0].value);
  const [zoneId, setZoneId] = useState('');
  const [threshold, setThreshold] = useState(5);
  const [severity, setSeverity] = useState('medium');
  const [cooldown, setCooldown] = useState(300);
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);

  const camera = useCamera(cameraId);
  const zones = useZones(cameraId || undefined);
  const ruleMeta = useMemo(() => RULE_TYPES.find((r) => r.value === ruleType)!, [ruleType]);

  const submit = async () => {
    setError(null);
    if (!cameraId) return setError('Select a camera.');
    if (ruleMeta.needs_zone && !zoneId) return setError('Select or create a zone.');
    try {
      await createRule.mutateAsync({
        camera_id: cameraId,
        zone_id: zoneId || null,
        name: name || ruleMeta.label,
        rule_type: ruleType,
        severity,
        cooldown_seconds: cooldown,
        config: { [ruleMeta.threshold_key]: threshold },
      });
      setName('');
      onCreated?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create the rule.');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">New rule</CardTitle>
        <CardDescription>Trigger an alert when a condition is met in a camera zone.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <Alert variant="destructive">{error}</Alert>}

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label>Camera</Label>
            <Select value={cameraId} onChange={(e) => { setCameraId(e.target.value); setZoneId(''); }}>
              <option value="">Select a camera…</option>
              {cameras.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Condition</Label>
            <Select value={ruleType} onChange={(e) => setRuleType(e.target.value)}>
              {RULE_TYPES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </Select>
          </div>
        </div>

        {cameraId && (
          <>
            <div className="space-y-1.5">
              <Label>Zone</Label>
              <Select value={zoneId} onChange={(e) => setZoneId(e.target.value)}>
                <option value="">Select a zone…</option>
                {zones.data?.map((z) => (
                  <option key={z.id} value={z.id}>
                    {z.name} ({z.zone_type})
                  </option>
                ))}
              </Select>
            </div>

            <details className="rounded-md border p-3">
              <summary className="cursor-pointer text-sm font-medium">Draw a new zone</summary>
              <div className="mt-3">
                <ZoneEditor cameraId={cameraId} thumbnailUrl={camera.data?.thumbnail_url} />
              </div>
            </details>
          </>
        )}

        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <Label>{ruleMeta.threshold_label}</Label>
            <Input
              type="number"
              min={1}
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Severity</Label>
            <Select value={severity} onChange={(e) => setSeverity(e.target.value)}>
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Cooldown (sec)</Label>
            <Input
              type="number"
              min={0}
              value={cooldown}
              onChange={(e) => setCooldown(Number(e.target.value))}
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label>Rule name (optional)</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder={ruleMeta.label} />
        </div>

        <Button onClick={submit} disabled={createRule.isPending}>
          {createRule.isPending ? 'Creating…' : 'Create rule'}
        </Button>
      </CardContent>
    </Card>
  );
}
