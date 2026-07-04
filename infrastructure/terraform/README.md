# Terraform — cloud infrastructure (optional, Phase 12)

Infrastructure-as-code for the reference cloud deployment. Planned modules:

```
terraform/
├── modules/
│   ├── network/         # VPC, subnets, security groups
│   ├── eks/             # managed Kubernetes + GPU node group
│   ├── rds/             # PostgreSQL/Aurora (+ TimescaleDB where supported)
│   ├── elasticache/     # Redis
│   └── s3/              # object storage buckets
└── environments/
    ├── staging/
    └── production/
```

Reference target is **AWS** (EKS + RDS + ElastiCache + S3); the design is
cloud-agnostic and portable to GCP/Azure. Populated in Phase 12.
