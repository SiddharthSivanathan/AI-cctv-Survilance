"""AI detection worker.

Consumes frames from the shared Redis stream (consumer group), runs YOLOv11s
detection + IOU tracking, and publishes detection results back to Redis. It is
**stateless and database-free** — the rule engine (Phase 8) consumes these
detections and decides what becomes a business event.
"""

from __future__ import annotations

import json
import threading
import time

import redis
import structlog

from src.config import get_settings
from src.detection.detector import YoloDetector
from src.detection.tracker import make_tracker
from src.detection.types import Detection
from src.tracking.registry import TrackRegistry
from src.redis_streams import (
    CONSUMER_GROUP,
    DETECTIONS_STREAM,
    FRAMES_STREAM,
    latest_detection_key,
)
from src.metrics.aggregator import MetricsAggregator
from src.metrics.emitter import MetricsEmitter
from src.rules.config_cache import RulesConfigCache
from src.rules.emitter import EventEmitter
from src.rules.engine import RuleEngine
from src.rules.geometry import foot_point, point_in_polygon

logger = structlog.get_logger("worker")


def build_payload(
    camera_id: str,
    detections: list[Detection],
    ts: float,
    durations: dict[int, float | None] | None = None,
) -> dict:
    """Pure builder for the detection payload published to Redis.

    ``durations`` maps track_id -> seconds-since-entry, added per detection so
    the live overlay can show how long each tracked object has been present.
    """
    durations = durations or {}
    people = [d for d in detections if d.class_name == "person"]
    items: list[dict] = []
    for det in detections:
        item = det.to_dict()
        if det.track_id is not None and durations.get(det.track_id) is not None:
            item["duration_s"] = durations[det.track_id]
        items.append(item)
    return {
        "camera_id": camera_id,
        "ts": ts,
        "person_count": len(people),
        "detections": items,
    }


class DetectionWorker:
    def __init__(self, client: redis.Redis, consumer_name: str = "worker-1") -> None:
        self._client = client
        self._settings = get_settings()
        self._consumer = consumer_name
        self._detector = YoloDetector()
        self._trackers: dict[str, object] = {}
        self._registries: dict[str, TrackRegistry] = {}
        self._rule_engine = RuleEngine()
        self._rules_config = RulesConfigCache()
        self._event_emitter = EventEmitter()
        self._metrics = MetricsAggregator()
        self._metrics_emitter = MetricsEmitter()

    def ensure_group(self) -> None:
        try:
            self._client.xgroup_create(FRAMES_STREAM, CONSUMER_GROUP, id="0", mkstream=True)
        except redis.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def run_forever(self, stop: threading.Event) -> None:
        self.ensure_group()
        while not stop.is_set():
            try:
                messages = self._client.xreadgroup(
                    CONSUMER_GROUP,
                    self._consumer,
                    {FRAMES_STREAM: ">"},
                    count=8,
                    block=2000,
                )
            except redis.RedisError as exc:
                logger.warning("xreadgroup_failed", error=str(exc))
                time.sleep(1)
                continue

            for _stream, entries in messages or []:
                for entry_id, fields in entries:
                    try:
                        self._process(fields)
                    except Exception as exc:  # noqa: BLE001 - never kill the loop
                        logger.warning("process_failed", error=str(exc))
                    finally:
                        self._client.xack(FRAMES_STREAM, CONSUMER_GROUP, entry_id)

    def _process(self, fields: dict) -> None:
        camera_id = _as_str(fields.get(b"camera_id") or fields.get("camera_id"))
        frame_bytes = fields.get(b"frame") or fields.get("frame")
        if not camera_id or not frame_bytes:
            return

        frame = self._decode(frame_bytes)
        if frame is None:
            return

        detections = self._detector.detect(frame)
        tracker = self._trackers.setdefault(camera_id, make_tracker())
        detections = tracker.update(detections)

        now = time.time()
        # Track lifecycle: entry/exit/duration per object.
        registry = self._registries.setdefault(camera_id, TrackRegistry())
        registry.observe(detections, now)
        durations = {
            d.track_id: registry.duration_for(d.track_id, now)
            for d in detections
            if d.track_id is not None
        }
        payload = build_payload(camera_id, detections, now, durations)
        self._publish(camera_id, payload)

        # Emit a summary when a track leaves (id, class, entry, exit, duration).
        for info in registry.sweep_ended(now):
            logger.info(
                "track_ended",
                camera_id=camera_id,
                track_id=info.track_id,
                object_class=info.class_name,
                confidence=round(info.best_confidence, 4),
                entry_ts=round(info.entry_ts, 2),
                exit_ts=round(info.last_seen_ts, 2),
                duration_s=round(info.duration, 2),
            )

        # Rule evaluation (in-worker, DB-free). Emits business events on change.
        self._rules_config.maybe_refresh(now)
        zones = self._rules_config.zones_for(camera_id)
        events = self._rule_engine.evaluate(
            camera_id, detections, self._rules_config.rules_for(camera_id), zones, now
        )
        if events:
            # Attach a snapshot of the firing frame to OPEN events (one encode).
            open_events = [e for e in events if e.status == "open"]
            if open_events:
                snapshot = self._encode_snapshot(frame)
                for event in open_events:
                    event.snapshot_b64 = snapshot
            self._event_emitter.emit(events)

        # Aggregated metrics (per-minute occupancy / footfall / queue).
        self._record_metrics(camera_id, detections, zones, now)

    def _record_metrics(self, camera_id: str, detections, zones, now: float) -> None:
        persons = [d for d in detections if d.class_name == "person"]
        queue_zones = [z for z in zones.values() if z.zone_type == "queue"]
        queue_count = sum(
            1
            for p in persons
            if any(point_in_polygon(foot_point(p.bbox), z.polygon) for z in queue_zones)
        )
        track_ids = {p.track_id for p in persons if p.track_id is not None}
        self._metrics.record(camera_id, len(persons), queue_count, track_ids, now)

        due = self._metrics.flush_due(now)
        if not due:
            return
        items: list[dict] = []
        for metric in due:
            meta = self._rules_config.meta_for(metric["camera_id"])
            if not meta:
                continue
            org_id, store_id = meta
            items.append(
                {"organization_id": org_id, "store_id": store_id or None, **metric}
            )
        self._metrics_emitter.emit(items)

    def _publish(self, camera_id: str, payload: dict) -> None:
        data = json.dumps(payload)
        self._client.xadd(
            DETECTIONS_STREAM,
            {"camera_id": camera_id, "payload": data},
            maxlen=self._settings.detections_stream_maxlen,
            approximate=True,
        )
        # Latest snapshot for the live overlay (short TTL).
        self._client.set(latest_detection_key(camera_id), data, ex=10)

    @staticmethod
    def _decode(frame_bytes: bytes):
        import cv2  # lazy: heavy native dep
        import numpy as np

        array = np.frombuffer(frame_bytes, dtype=np.uint8)
        return cv2.imdecode(array, cv2.IMREAD_COLOR)

    @staticmethod
    def _encode_snapshot(frame) -> str | None:
        """Encode a BGR frame to a base64 JPEG for event snapshots."""
        import base64

        import cv2

        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if not ok:
            return None
        return base64.b64encode(buf.tobytes()).decode("ascii")


def _as_str(value) -> str:
    if isinstance(value, bytes):
        return value.decode()
    return str(value) if value is not None else ""
