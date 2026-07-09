"""YOLOv11s object detector.

The Ultralytics model is loaded lazily so importing this module never pulls in
torch. The raw-result → Detection parsing is a pure function (`parse_results`)
so it can be unit-tested without the model.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import structlog

from src.config import DEFAULT_CLASSES, get_settings
from src.detection.types import Detection

logger = structlog.get_logger("detector")


def parse_results(
    rows: Iterable[Sequence[float]],
    *,
    class_map: dict[int, str],
    allowed_ids: set[int],
    min_confidence: float,
) -> list[Detection]:
    """Convert raw YOLO rows [x1, y1, x2, y2, conf, cls] into Detections.

    Pure function — the single place detection filtering logic lives.
    """
    detections: list[Detection] = []
    for row in rows:
        x1, y1, x2, y2, conf, cls = row
        class_id = int(cls)
        if class_id not in allowed_ids or conf < min_confidence:
            continue
        detections.append(
            Detection(
                class_id=class_id,
                class_name=class_map.get(class_id, str(class_id)),
                confidence=float(conf),
                bbox=(float(x1), float(y1), float(x2), float(y2)),
            )
        )
    return detections


class YoloDetector:
    """Ultralytics YOLOv11s wrapper. Model loaded on first use."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._model = None
        self._device: str | None = None
        self._allowed = set(self._settings.class_ids)

    def _resolve_device(self) -> str:
        """Pick the inference device. Uses CUDA only when it is actually
        available; otherwise falls back to CPU. ``ai_device`` may be
        "auto" (prefer CUDA), "cuda" (prefer CUDA), or "cpu" (force CPU)."""
        configured = self._settings.ai_device.lower()
        if configured == "cpu":
            return "cpu"
        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
        except Exception:  # noqa: BLE001 - torch/CUDA probing must never crash inference
            pass
        if configured == "cuda":
            logger.warning("cuda_requested_but_unavailable", falling_back_to="cpu")
        return "cpu"

    def _ensure_model(self):
        if self._model is None:
            from ultralytics import YOLO  # imported lazily (pulls torch)

            self._device = self._resolve_device()
            logger.info(
                "loading_model",
                model=self._settings.model_name,
                configured_device=self._settings.ai_device,
                resolved_device=self._device,
            )
            self._model = YOLO(self._settings.model_name)
        return self._model

    def detect(self, frame) -> list[Detection]:
        """Run detection on a BGR numpy frame and return filtered Detections."""
        model = self._ensure_model()
        results = model.predict(
            frame,
            imgsz=self._settings.model_imgsz,
            conf=self._settings.model_confidence,
            classes=self._settings.class_ids,
            device=self._device,
            verbose=False,
        )
        if not results:
            return []
        boxes = results[0].boxes
        rows = boxes.data.tolist() if boxes is not None else []
        return parse_results(
            rows,
            class_map=DEFAULT_CLASSES,
            allowed_ids=self._allowed,
            min_confidence=self._settings.model_confidence,
        )
