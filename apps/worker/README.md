# @visionops/worker

VisionOps AI background workers — Celery + Beat.

## Responsibility
Async jobs off the request path: **rule evaluation** (Phase 8), **notification
fanout** (Phase 10), **report generation** (Phase 10, Beat-scheduled), and
billing jobs (Phase 11). Broker + result backend = Redis.

## Develop
```bash
pip install -e ".[dev]"
celery -A src.celery_app worker --beat --loglevel=info
pytest -q
```

## Phase 2 scope
Broker wiring + task discovery + a `visionops.ping` liveness task. No domain
tasks yet.
