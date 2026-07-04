# Database migrations (Alembic)

The database URL is injected from application settings (`migrations/env.py`),
not from `alembic.ini`.

```bash
# create a migration (autogenerate from ORM models)
alembic revision --autogenerate -m "feat(api): add organizations"

# apply / roll back
alembic upgrade head
alembic downgrade -1
```

No versioned migrations exist yet — the schema lands in **Phase 3**.
