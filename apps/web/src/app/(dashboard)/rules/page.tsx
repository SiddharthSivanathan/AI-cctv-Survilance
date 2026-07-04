'use client';

import { Button, Card, CardContent, CardHeader, CardTitle, Skeleton, Switch } from '@visionops/ui';
import { RuleBuilder } from '@/features/rules/rule-builder';
import { useDeleteRule, useRules, useUpdateRule } from '@/features/rules/hooks';
import { RULE_TYPES } from '@/features/rules/types';
import { SeverityBadge } from '@/features/events/severity';

function ruleLabel(type: string): string {
  return RULE_TYPES.find((r) => r.value === type)?.label ?? type;
}

export default function RulesPage() {
  const { data: rules, isLoading } = useRules();
  const updateRule = useUpdateRule();
  const deleteRule = useDeleteRule();

  return (
    <div className="mx-auto max-w-4xl px-8 py-10">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Rules</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          No-code business rules. When a condition is met, an alert is raised.
        </p>
      </div>

      <div className="mb-8">
        <RuleBuilder />
      </div>

      <h2 className="mb-3 text-lg font-semibold tracking-tight">Your rules</h2>
      {isLoading && <Skeleton className="h-24" />}
      {!isLoading && rules?.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            No rules yet. Create one above.
          </CardContent>
        </Card>
      )}
      {!isLoading && rules && rules.length > 0 && (
        <div className="space-y-3">
          {rules.map((rule) => (
            <Card key={rule.id}>
              <CardHeader className="flex-row items-center justify-between space-y-0 py-4">
                <div className="flex items-center gap-3">
                  <CardTitle className="text-base">{rule.name}</CardTitle>
                  <SeverityBadge severity={rule.severity} />
                  <span className="text-xs text-muted-foreground">{ruleLabel(rule.rule_type)}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Switch
                    checked={rule.enabled}
                    onCheckedChange={(v) => updateRule.mutate({ id: rule.id, data: { enabled: v } })}
                    aria-label="Enabled"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteRule.mutate(rule.id)}
                  >
                    Delete
                  </Button>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
