# Kubernetes manifests / Helm charts

Production deployment lives here (**Phase 12**). Planned structure:

```
kubernetes/
├── base/                # kustomize base (deployments, services, configmaps)
├── overlays/
│   ├── staging/
│   └── production/
└── charts/              # Helm charts per service
```

Key production concerns handled in Phase 12:
- **GPU node pools** for `ai-engine` (NVIDIA device plugin, node selectors/taints).
- HorizontalPodAutoscalers for API + inference.
- Secrets via external-secrets/KMS (never plain manifests).
- Ingress + cert-manager (TLS).
- PodDisruptionBudgets, resource requests/limits, network policies.

Intentionally empty until Phase 12 to keep earlier phases focused.
