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
from src.detection.tracker import IouTracker
from src.detection.types import Detection
from src.redis_streams import (
    CONSUMER_GROUP,
    DETECTIONS_STREAM,
    FRAMES_STREAM,
    latest_detection_key,
)
from src.rules.config_cache import RulesConfigCache
from src.rules.emitter import EventEmitter
from src.rules.engine import RuleEngine

logger = structlog.get_logger("worker")


def build_payload(camera_id: str, detections: list[Detection], ts: float) -> dict:
    """Pure builder for the detection payload published to Redis."""
    people = [d for d in detections if d.class_name == "person"]
    return {
        "camera_id": camera_id,
        "ts": ts,
        "person_count": len(people),
        "detections": [d.to_dict() for d in detections],
    }


class DetectionWorker:
    def __init__(self, client: redis.Redis, consumer_name: str = "worker-1") -> None:
        self._client = client
        self._settings = get_settings()
        self._consumer = consumer_name
        self._detector = YoloDetector()
        self._trackers: dict[str, IouTracker] = {}
        self._rule_engine = RuleEngine()
        self._rules_config = RulesConfigCache()
        self._event_emitter = EventEmitter()

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
        tracker = self._trackers.setdefault(camera_id, IouTracker())
        detections = tracker.update(detections)

        now = time.time()
        payload = build_payload(camera_id, detections, now)
        self._publish(camera_id, payload)

        # Rule evaluation (in-worker, DB-free). Emits business events on change.
        self._rules_config.maybe_refresh(now)
        events = self._rule_engine.evaluate(
            camera_id,
            detections,
            self._rules_config.rules_for(camera_id),
            self._rules_config.zones_for(camera_id),
            now,
        )
        if events:
            self._event_emitter.emit(events)

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


def _as_str(value) -> str:
    if isinstance(value, bytes):
        return value.decode()
    return str(value) if value is not None else ""
