"""In-worker rule engine.

Evaluates detections against per-camera rules + zones, maintains ephemeral
in-memory state (dwell timers, occupancy, open events, cooldowns), and produces
business events with an OPEN → RESOLVED lifecycle. It never touches the
database — events are published to the API Event Service.

Designed behind a clean interface so it can be extracted into its own service
in V2 without changing the detection pipeline.
"""
